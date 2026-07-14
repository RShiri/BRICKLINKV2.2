#!/usr/bin/env python3
"""Run the BrickLink pipeline over a list of sets and print their USED price.

This drives the *real* scraper + PriceAnalyzer, so it reflects the current
code — including the incomplete-set filtering fix. Use it to see the fix's
effect on actual BrickLink data (this repo can't reach bricklink.com from a
sandbox, so run it on a machine with normal network access).

Before/after the fix
--------------------
    git checkout main            && python scripts/price_sets.py --csv before.csv
    git checkout <this-branch>   && python scripts/price_sets.py --csv after.csv
Then diff before.csv / after.csv — sets whose used price moves are the ones
that had incomplete listings dragging the average down.

Usage
-----
    python scripts/price_sets.py                 # all 32 default sets, fresh scrape
    python scripts/price_sets.py 75331 75304     # only these IDs
    python scripts/price_sets.py --use-cache     # reuse DB cache (skip re-scrape)
    python scripts/price_sets.py --selenium      # use the Selenium scraper
    python scripts/price_sets.py --csv out.csv   # choose the CSV path

Notes
-----
* Prices come out in ILS (the pipeline's base currency); a USD column is added
  from live FX when available.
* Fresh scraping is the default (--use-cache to opt out) so a stale pre-fix
  cache entry can't mask the change.
* Runs even without Supabase configured (falls back to an in-memory cache).
"""
import argparse
import csv
import os
import sys

# Make the repo root importable no matter where this is launched from.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from pricing_engine import PriceAnalyzer

# (set number, friendly name) — the seller's list.
DEFAULT_SETS = [
    ("75331", "Razor Crest - UCS"),
    ("75304", "Darth Vader Helmet"),
    ("75328", "The Mandalorian Helmet"),
    ("75349", "Captain Rex Helmet"),
    ("75387", "Boarding the Tantive IV"),
    ("40765", "Kamino Training Facility (GWP)"),
    ("75375", "Millennium Falcon - midi-scale"),
    ("42115", "Lamborghini Sian FKP 37"),
    ("40806", "Gingerbread AT-AT"),
    ("76216", "Iron Man Armory"),
    ("76191", "Infinity Gauntlet"),
    ("76223", "Nano Gauntlet"),
    ("76321", "Spider-Man vs. Doc Ock Subway Train"),
    ("76261", "Spider-Man Final Battle"),
    ("77253", "Bugatti Vision GT"),
    ("76210", "Hulkbuster"),
    ("75397", "Jabba's Sail Barge - UCS"),
    ("75308", "R2-D2 - UCS"),
    ("75353", "Endor Speeder Chase"),
    ("43217", "Up House"),
    ("77255", "Lightning McQueen (Cars)"),
    ("21357", "Luxo Jr."),
    ("42222", "Bugatti Chiron Pur Sport"),
    ("76248", "The Avengers Quinjet"),
    ("40913", "Vintage Parade Car (GWP)"),
    ("42213", "Ford Bronco"),
    ("76917", "Nissan Skyline GT-R R34"),
    ("21358", "Minifigure Vending Machine"),
    ("40699", "Retro Record Player (GWP)"),
    ("76269", "Avengers Tower"),
    ("76178", "Daily Bugle"),
    ("40766", "Tribute to Jane Austen's Books (GWP)"),
]


class _NullDB:
    """In-memory stand-in so the scraper runs without Supabase configured."""

    def get_item(self, item_id):
        return None

    def save_item(self, item_id, data):
        pass

    def get_inventory(self, set_id):
        return (None, None)

    def save_inventory(self, set_id, data):
        pass


def _make_db():
    """Real DB if it's configured (uses its cache); otherwise a null stand-in."""
    try:
        from database import Database
        return Database()
    except Exception as exc:  # noqa: BLE001 - any config/connection failure
        print(f"[warn] DB unavailable ({exc}); using in-memory cache",
              file=sys.stderr)
        return _NullDB()


def _make_scraper(use_selenium):
    """Instantiate a scraper, injecting a DB so it works standalone.

    We bypass the scraper's __init__ (which hard-requires Database()) and set
    up the same attributes ourselves, so the script runs even without secrets.
    """
    db = _make_db()
    if use_selenium:
        from scraper import BrickLinkScraper as Cls
        scraper = Cls.__new__(Cls)
        scraper.db = db
        scraper.current_type = "S"
        scraper.driver = None  # lazily initialised on first scrape
    else:
        from scraper_playwright import BrickLinkScraperV2 as Cls
        scraper = Cls.__new__(Cls)
        scraper.db = db
        scraper.current_type = "S"
        scraper.playwright = None
        scraper.browser = None
        scraper.context = None
        scraper._init_browser()
    return scraper


def _ils_to_usd(amount):
    """Convert an ILS figure to USD using live FX; None if unavailable."""
    try:
        from etl.currency import get_rates
        rate = get_rates().get("USD")  # USD -> ILS
        if rate:
            return round(amount / rate, 2)
    except Exception:  # noqa: BLE001 - FX is best-effort
        pass
    return None


def price_one(scraper, set_id, name, force):
    """Scrape + analyze one set; return a result row (never raises)."""
    row = {"num": set_id, "name": name, "used_ils": None, "used_usd": None,
           "confidence": "ERROR", "new_ils": None, "year": None, "note": ""}
    try:
        data = scraper.scrape(set_id, item_type="S", force=force)
        if not data or "error" in data:
            row["note"] = (data or {}).get("error", "no data")
            return row
        res = PriceAnalyzer(data).analyze()
        used = res.get("used", {})
        row["used_ils"] = used.get("market_price")
        row["confidence"] = used.get("confidence", "?")
        row["new_ils"] = res.get("new", {}).get("market_price")
        row["year"] = res.get("meta", {}).get("year_released")
        if row["used_ils"] is not None:
            row["used_usd"] = _ils_to_usd(row["used_ils"])
    except Exception as exc:  # noqa: BLE001 - keep going on a single bad set
        row["note"] = f"{type(exc).__name__}: {exc}"
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ids", nargs="*", help="Set IDs to price (default: the 32-set list)")
    ap.add_argument("--use-cache", action="store_true",
                    help="Reuse DB cache instead of re-scraping (default: fresh scrape)")
    ap.add_argument("--selenium", action="store_true",
                    help="Use the Selenium scraper instead of Playwright")
    ap.add_argument("--csv", default="used_prices.csv", help="CSV output path")
    args = ap.parse_args()

    sets = [(i, i) for i in args.ids] if args.ids else DEFAULT_SETS
    force = not args.use_cache

    print(f"Pricing {len(sets)} set(s) | scraper={'selenium' if args.selenium else 'playwright'} "
          f"| {'FRESH scrape' if force else 'using cache'}\n")

    scraper = _make_scraper(args.selenium)
    results = []
    try:
        for set_id, name in sets:
            r = price_one(scraper, set_id, name, force)
            results.append(r)
            ils = f"{r['used_ils']:.0f}" if r["used_ils"] is not None else "-"
            usd = f"${r['used_usd']:.0f}" if r["used_usd"] is not None else "-"
            print(f"  {set_id:<7} {name[:36]:<36} used={ils:>7} ILS  {usd:>6}  "
                  f"[{r['confidence']}] {r['note']}")
    finally:
        try:
            scraper.close()
        except Exception:  # noqa: BLE001
            pass

    with open(args.csv, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["set_no", "name", "used_ils", "used_usd", "confidence",
                    "new_ils", "year", "note"])
        for r in results:
            w.writerow([r["num"], r["name"], r["used_ils"], r["used_usd"],
                        r["confidence"], r["new_ils"], r["year"], r["note"]])

    ok = sum(1 for r in results if r["used_ils"] is not None)
    print(f"\nDone: {ok}/{len(results)} priced. CSV -> {args.csv}")


if __name__ == "__main__":
    main()
