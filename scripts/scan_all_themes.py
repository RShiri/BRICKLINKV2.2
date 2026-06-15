"""
scan_all_themes.py — Comprehensive LEGO minifigure scraper.
Run this on your LOCAL machine (needs Chrome + BrickLink credentials).

Two strategies run in order:
  1. Catalog discovery  — Crawls BrickLink's full minifig category tree
     page-by-page to collect the real item IDs for every theme.
     This is the primary strategy: it finds the EXACT IDs BrickLink uses
     regardless of zero-padding, and handles all categories automatically.

  2. Prefix-range scan — Iterates known theme prefixes numerically as a
     backup to catch anything the catalog phase missed.
     Uses the correct zero-padding per theme (3 vs 4 digits).

Usage (run from project root):
    python scripts/scan_all_themes.py                # full scan (recommended)
    python scripts/scan_all_themes.py --catalog-only # only catalog discovery
    python scripts/scan_all_themes.py --prefix-only  # only numeric range scan
    python scripts/scan_all_themes.py --resume       # continue interrupted scan
    python scripts/scan_all_themes.py --clear-state  # wipe saved state + start fresh

Requirements (install once):
    pip install selenium beautifulsoup4 psycopg2-binary
    # Also need Chrome + matching chromedriver in PATH

Expected runtime: 8-24 hours for a full scan (thousands of minifigs).
Interrupt at any time with Ctrl+C — state is saved every 200 items.
Re-run with --resume to continue.
"""

import time, sys, os, json, argparse, re, random, logging
from datetime import datetime
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper import BrickLinkScraper
from database import Database

logging.basicConfig(level=logging.INFO, format="%(message)s")

# ---------------------------------------------------------------------------
# Zero-padding rules per theme prefix
#
# BrickLink ID format varies by theme:
#   4-digit (sw0001, sh0001):  Star Wars, Superheroes
#   3-digit (hp001, njo001):   everything else
#
# PREFIX_RANGES: prefix → (start, end, digits)
# ---------------------------------------------------------------------------
PREFIX_RANGES = {
    # ── 4-digit themes ──────────────────────────────────────────────────────
    "sw":   (1, 2000, 4),   # Star Wars          sw0001–sw2000
    "sh":   (1, 1300, 4),   # Superheroes (all)  sh0001–sh1300

    # ── 3-digit themes ──────────────────────────────────────────────────────
    "hp":   (1, 600,  3),   # Harry Potter       hp001–hp600
    "njo":  (1, 1000, 3),   # Ninjago            njo001–njo999
    "col":  (1, 700,  3),   # CMF Series         col001–col700
    "tlm":  (1, 300,  3),   # The LEGO Movie     tlm001–tlm300
    "lor":  (1, 300,  3),   # Lord of the Rings  lor001–lor300
    "hob":  (1, 150,  3),   # The Hobbit         hob001–hob150
    "jw":   (1, 200,  3),   # Jurassic World     jw001–jw200
    "iaj":  (1, 100,  3),   # Indiana Jones      iaj001–iaj100
    "poc":  (1, 120,  3),   # Pirates Caribbean  poc001–poc120
    "loc":  (1, 200,  3),   # Legends of Chima   loc001–loc200
    "nex":  (1, 150,  3),   # Nexo Knights       nex001–nex150
    "elf":  (1, 100,  3),   # Elves              elf001–elf100
    "frnd": (1, 400,  3),   # Friends            frnd001–frnd400
    "toy":  (1, 100,  3),   # Toy Story          toy001–toy100
    "sc":   (1, 100,  3),   # Speed Champions    sc001–sc100
    "hs":   (1, 100,  3),   # Hidden Side        hs001–hs100
    "mk":   (1, 250,  3),   # Monkie Kid         mk001–mk250
    "cty":  (1, 2000, 3),   # City / Town        cty001–cty999
    "cas":  (1, 500,  3),   # Castle             cas001–cas500
    "bat":  (1, 400,  3),   # Batman Movie       bat001–bat400
    "dim":  (1, 200,  3),   # Dimensions         dim001–dim200
    "idea": (1, 200,  3),   # Ideas              idea001–idea200
    "twn":  (1, 600,  3),   # Classic Town       twn001–twn600
    "pi":   (1, 200,  3),   # Classic Pirates    pi001–pi200
    "sp":   (1, 150,  3),   # Classic Space      sp001–sp150
    "kni":  (1, 200,  3),   # Kingdoms           kni001–kni200
    "adv":  (1, 150,  3),   # Adventurers        adv001–adv150
    "pm":   (1, 100,  3),   # Power Miners       pm001–pm100
    "res":  (1, 100,  3),   # Rescue             res001–res100
    "agt":  (1, 200,  3),   # Agents             agt001–agt200
    "atl":  (1, 100,  3),   # Atlantis           atl001–atl100
    "pha":  (1, 100,  3),   # Pharaoh's Quest    pha001–pha100
    "gal":  (1, 100,  3),   # Galaxy Squad       gal001–gal100
    "dis":  (1, 250,  3),   # Disney             dis001–dis250
    "dp":   (1, 150,  3),   # Disney Princess    dp001–dp150
    "uni":  (1, 100,  3),   # Unikitty           uni001–uni100
    "alp":  (1, 100,  3),   # Alpha Team         alp001–alp100
    "rac":  (1, 100,  3),   # Racers             rac001–rac100
    "exo":  (1, 100,  3),   # Exo-Force          exo001–exo100
    "min":  (1, 200,  3),   # Minecraft          min001–min200
    "fst":  (1, 100,  3),   # Fright Knights     fst001–fst100
}

# Gap detection
MAX_CONSECUTIVE_FAILURES = 40  # Try 40 IDs before skipping
SKIP_AHEAD = 80                # IDs to skip after gap detected

# Rate limiting
BASE_DELAY   = 0.6  # seconds between requests
JITTER       = 0.4  # random extra 0–0.4 s

# State file for resume
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_state.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_fresh(cached_item, max_days: int = 30) -> bool:
    if not cached_item or "error" in cached_item:
        return False
    ts = (cached_item.get("meta", {}).get("timestamp") or
          cached_item.get("meta", {}).get("cache_date", ""))
    if not ts:
        return False
    try:
        last_date = datetime.fromisoformat(str(ts).split("T")[0])
        return (datetime.now() - last_date).days < max_days
    except Exception:
        return True


def _scrape_one(scraper, db, item_id: str, counters: dict) -> str:
    """Scrape one item. Returns 'cached' | 'scraped' | 'error'."""
    cached_item = db.get_item(item_id)
    if _is_fresh(cached_item):
        counters["cached"] += 1
        return "cached"

    time.sleep(BASE_DELAY + random.uniform(0, JITTER))
    try:
        data = scraper.scrape(item_id, item_type="M", force=False)
        if "error" in data:
            counters["errors"] += 1
            return "error"
        counters["scraped"] += 1
        return "scraped"
    except Exception:
        counters["errors"] += 1
        return "error"


def _status(item_id, c, extra=""):
    sys.stdout.write(
        f"\r  {item_id:<14}  💾{c['cached']}  🌐{c['scraped']}  ❌{c['errors']}  {extra}   "
    )
    sys.stdout.flush()


def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_state(state: dict):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Phase 1 — Catalog discovery (finds exact BrickLink IDs with pagination)
# ---------------------------------------------------------------------------

def discover_categories(driver) -> dict:
    """Return {cat_id: category_name} from BrickLink's minifig catalog tree."""
    print("\n🔍  Discovering categories from BrickLink catalog tree…")
    driver.get("https://www.bricklink.com/catalogTree.asp?itemType=M")
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cats = {}
    for link in soup.find_all("a", href=re.compile(r"catID=\d+")):
        m = re.search(r"catID=(\d+)", link.get("href", ""))
        name = link.get_text(strip=True)
        if m and name:
            cats[m.group(1)] = name

    print(f"  Found {len(cats)} categories.")
    return cats


def get_category_items_all_pages(driver, cat_id: str, cat_name: str) -> list:
    """Scrape every page of a category listing and return real item IDs."""
    item_ids = []
    page = 1

    while True:
        url = (f"https://www.bricklink.com/catalogList.asp"
               f"?catType=M&catID={cat_id}&pg={page}")
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            found = []
            for link in soup.find_all("a", href=re.compile(r"[?&]M=")):
                m = re.search(r"[?&]M=([A-Za-z0-9\-]+)", link.get("href", ""))
                if m:
                    mid = m.group(1)
                    if mid not in item_ids and mid not in found:
                        found.append(mid)

            if not found:
                break  # empty page → done

            item_ids.extend(found)
            print(f"      Page {page}: +{len(found)} items  (running total: {len(item_ids)})")

            # Check for a next-page link
            has_next = any(
                re.search(rf"pg={page + 1}", a.get("href", ""))
                for a in soup.find_all("a", href=True)
            )
            if not has_next:
                break

            page += 1
            time.sleep(1)

        except Exception as e:
            print(f"      ⚠️  Page {page} error: {e}")
            break

    return item_ids


def run_catalog_phase(scraper, db, state: dict, totals: dict):
    print("\n" + "=" * 70)
    print("  PHASE 1 — CATALOG DISCOVERY")
    print("=" * 70)

    driver = scraper._init_driver()
    categories = discover_categories(driver)
    if not categories:
        print("  ❌ No categories found, skipping phase 1.")
        return

    done_cats  = set(state.get("completed_categories", []))
    all_seen   = set(state.get("discovered_ids", []))

    for cat_id, cat_name in sorted(categories.items(), key=lambda x: x[1]):
        if cat_id in done_cats:
            print(f"  ⏭️   {cat_name}  (already done)")
            continue

        print(f"\n  📦  {cat_name}  (catID={cat_id})")
        item_ids = get_category_items_all_pages(driver, cat_id, cat_name)
        new_ids  = [i for i in item_ids if i not in all_seen]
        print(f"      {len(item_ids)} items found, {len(new_ids)} new to scrape")

        counters = {"cached": 0, "scraped": 0, "errors": 0}
        for item_id in new_ids:
            _status(item_id, counters)
            result = _scrape_one(scraper, db, item_id, counters)
            if result == "scraped":
                name = (db.get_item(item_id) or {}).get("meta", {}).get("item_name", "?")
                print(f"\n    ✨  {item_id} — {name}")
            all_seen.add(item_id)

        print(f"\n      Summary: 💾{counters['cached']}  🌐{counters['scraped']}  ❌{counters['errors']}")
        for k in totals:
            totals[k] += counters[k]

        done_cats.add(cat_id)
        state["completed_categories"] = list(done_cats)
        state["discovered_ids"] = list(all_seen)
        _save_state(state)

    print("\n✅  Catalog phase complete.")


# ---------------------------------------------------------------------------
# Phase 2 — Prefix-range scan (numeric backup with correct padding)
# ---------------------------------------------------------------------------

def run_prefix_phase(scraper, db, state: dict, totals: dict):
    print("\n" + "=" * 70)
    print("  PHASE 2 — PREFIX-RANGE SCAN")
    print("=" * 70)
    print(f"  {len(PREFIX_RANGES)} prefixes configured\n")

    done_pfx   = set(state.get("completed_prefixes", []))
    pfx_pos    = state.get("prefix_position", {})   # {prefix: last_num_checked}

    for prefix, (start, end, digits) in PREFIX_RANGES.items():
        if prefix in done_pfx:
            print(f"  ⏭️   {prefix.upper()}  (already done)")
            continue

        resume_at = pfx_pos.get(prefix, start)
        fmt = f"{{:0{digits}d}}"   # e.g. "{:04d}" or "{:03d}"
        print(f"\n  🎨  {prefix.upper()}  "
              f"(#{prefix}{fmt.format(resume_at)} – {prefix}{fmt.format(end)}, {digits}-digit)")

        counters = {"cached": 0, "scraped": 0, "errors": 0}
        consecutive = 0
        num = resume_at

        while num <= end:
            item_id = f"{prefix}{fmt.format(num)}"
            _status(item_id, counters, f"[{num}/{end}]")

            result = _scrape_one(scraper, db, item_id, counters)

            if result == "error":
                consecutive += 1
                if consecutive >= MAX_CONSECUTIVE_FAILURES:
                    print(f"\n    ⚠️  {MAX_CONSECUTIVE_FAILURES} consecutive misses — "
                          f"skipping {SKIP_AHEAD} IDs")
                    num += SKIP_AHEAD
                    consecutive = 0
                    continue
            else:
                consecutive = 0
                if result == "scraped":
                    name = (db.get_item(item_id) or {}).get("meta", {}).get("item_name", "?")
                    print(f"\n    ✨  {item_id} — {name}")

            num += 1

            # Checkpoint every 200 items
            if num % 200 == 0:
                pfx_pos[prefix] = num
                state["prefix_position"] = pfx_pos
                _save_state(state)

        print(f"\n      Summary: 💾{counters['cached']}  🌐{counters['scraped']}  ❌{counters['errors']}")
        for k in totals:
            totals[k] += counters[k]

        done_pfx.add(prefix)
        state["completed_prefixes"] = list(done_pfx)
        pfx_pos.pop(prefix, None)
        state["prefix_position"] = pfx_pos
        _save_state(state)

    print("\n✅  Prefix-range phase complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive LEGO minifig scraper — run on your local machine."
    )
    parser.add_argument("--catalog-only",  action="store_true",
                        help="Only run Phase 1 (catalog discovery)")
    parser.add_argument("--prefix-only",   action="store_true",
                        help="Only run Phase 2 (numeric prefix scan)")
    parser.add_argument("--resume",        action="store_true",
                        help="Resume from saved scan_state.json")
    parser.add_argument("--clear-state",   action="store_true",
                        help="Delete saved state and start fresh")
    args = parser.parse_args()

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 70)
    print("  COMPREHENSIVE LEGO MINIFIGURE SCRAPER")
    print("=" * 70)
    phases = "Catalog + Prefix-range"
    if args.catalog_only:  phases = "Catalog only"
    if args.prefix_only:   phases = "Prefix-range only"
    print(f"  Phases:   {phases}")
    print(f"  Padding:  4-digit for sw/sh, 3-digit for all other themes")
    print(f"  Cache:    skip items scraped in last 30 days")
    print(f"  Delay:    {BASE_DELAY}–{BASE_DELAY+JITTER:.1f} s per request")
    print(f"  Gap skip: {SKIP_AHEAD} IDs after {MAX_CONSECUTIVE_FAILURES} consecutive failures")

    if args.clear_state and os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print("\n  🗑️   State file cleared.")

    state = _load_state() if args.resume else {}
    if state:
        print(f"\n  ▶️   Resuming — "
              f"{len(state.get('completed_categories', []))} categories done, "
              f"{len(state.get('completed_prefixes', []))} prefixes done")

    print("\n  Press ENTER to start  (Ctrl+C saves state and stops cleanly)…")
    input()

    db = Database()
    scraper = BrickLinkScraper()
    totals = {"cached": 0, "scraped": 0, "errors": 0}
    t0 = time.time()

    try:
        if not args.prefix_only:
            run_catalog_phase(scraper, db, state, totals)
        if not args.catalog_only:
            run_prefix_phase(scraper, db, state, totals)

    except KeyboardInterrupt:
        print("\n\n  🛑  Stopped — progress saved to scan_state.json")
        print("     Re-run with --resume to continue.")
    finally:
        scraper.close()
        db.close()
        elapsed = time.time() - t0
        total = totals["cached"] + totals["scraped"]

        print("\n\n" + "=" * 70)
        print("  SCAN SUMMARY")
        print("=" * 70)
        print(f"  ⏱️   Time:     {elapsed/60:.1f} min  ({elapsed/3600:.2f} h)")
        print(f"  💾  Cached:   {totals['cached']:,}  (already in DB)")
        print(f"  🌐  Scraped:  {totals['scraped']:,}  (newly added)")
        print(f"  ❌  Errors:   {totals['errors']:,}  (not found / failed)")
        print(f"  📦  Total:    {total:,}  minifigures processed")
        print("=" * 70)

        if totals["scraped"]:
            print(f"\n  ✅  {totals['scraped']:,} new minifigures added to your database!")
        print("  💡  Open the dashboard and browse any category page to see results.\n")

        # Clean up state file if fully done
        if (len(state.get("completed_prefixes", [])) == len(PREFIX_RANGES)
                and not args.catalog_only):
            try:
                os.remove(STATE_FILE)
                print("  🗑️   State file removed (scan fully complete).")
            except Exception:
                pass


if __name__ == "__main__":
    main()
