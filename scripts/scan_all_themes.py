"""
scan_all_themes.py — Comprehensive LEGO minifigure scraper.

Two complementary strategies run in order:
  1. Catalog discovery — fetches every BrickLink minifig category page
     (with pagination) and collects real item IDs.
  2. Prefix-range scan — iterates known theme prefixes numerically to
     catch items that live outside standard category pages or whose
     catalog pages failed to load.

Run:
    cd /home/user/BRICKLINKV2.2
    python scripts/scan_all_themes.py               # full scan
    python scripts/scan_all_themes.py --prefix-only # skip catalog discovery
    python scripts/scan_all_themes.py --catalog-only
    python scripts/scan_all_themes.py --resume      # resume from state file
"""

import time, sys, os, json, argparse, re, logging
from datetime import datetime
from bs4 import BeautifulSoup

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper import BrickLinkScraper
from database import Database

logging.basicConfig(level=logging.INFO, format="%(message)s")

# ---------------------------------------------------------------------------
# Theme prefix → (start, end) for numeric range scan
# These are conservative maximums — smart gap detection stops early anyway
# ---------------------------------------------------------------------------
PREFIX_RANGES = {
    # Licensed themes
    "sh":   (1, 1200),   # Superheroes (Marvel + DC)
    "sw":   (1, 2000),   # Star Wars
    "hp":   (1, 600),    # Harry Potter / Wizarding World
    "njo":  (1, 1000),   # Ninjago
    "col":  (1, 700),    # Collectible Minifigures (Series 1-25+)
    "tlm":  (1, 300),    # The LEGO Movie 1 & 2
    "lor":  (1, 300),    # Lord of the Rings
    "hob":  (1, 150),    # The Hobbit
    "jw":   (1, 200),    # Jurassic World / Park
    "iaj":  (1, 100),    # Indiana Jones
    "poc":  (1, 120),    # Pirates of the Caribbean
    "loc":  (1, 200),    # Legends of Chima
    "nex":  (1, 150),    # Nexo Knights
    "elf":  (1, 100),    # Elves
    "frnd": (1, 400),    # Friends
    "toy":  (1, 100),    # Toy Story
    "sc":   (1, 100),    # Speed Champions
    "hs":   (1, 100),    # Hidden Side
    "mk":   (1, 250),    # Monkie Kid
    "cty":  (1, 2000),   # City / Town
    # Classic/older themes
    "cas":  (1, 500),    # Castle
    "bat":  (1, 400),    # The LEGO Batman Movie
    "dim":  (1, 200),    # Dimensions
    "idea": (1, 200),    # Ideas
    "twn":  (1, 600),    # Classic Town
    "pi":   (1, 200),    # Classic Pirates
    "sp":   (1, 150),    # Classic Space
    "kni":  (1, 200),    # Kingdoms
    "adv":  (1, 150),    # Adventurers
    "pm":   (1, 100),    # Power Miners
    "res":  (1, 100),    # Rescue
    "agt":  (1, 200),    # Agents
    "atl":  (1, 100),    # Atlantis
    "pha":  (1, 100),    # Pharaoh's Quest
    "gal":  (1, 100),    # Galaxy Squad
    "dis":  (1, 250),    # Disney
    "dp":   (1, 150),    # Disney Princess
    "ww":   (1, 150),    # Wizarding World extras
    "hpn":  (1, 100),    # Harry Potter alternate prefix
    "uni":  (1, 100),    # Unikitty
    "elc":  (1, 100),    # Elves alternate prefix
    "fst":  (1, 100),    # Fright Knights / misc Space
    "alp":  (1, 100),    # Alpha Team
    "rac":  (1, 100),    # Racers
    "exo":  (1, 100),    # Exo-Force
    "bio":  (1, 100),    # Bionicle
    "min":  (1, 200),    # Minecraft
    "mar":  (1, 100),    # Marvel extra
    "dcs":  (1, 200),    # DC Super Heroes extra
}

# Gap detection: skip ahead after this many consecutive 404/errors
MAX_CONSECUTIVE_FAILURES = 40
SKIP_AHEAD = 80

# Seconds between scrape requests (base delay, jitter added)
BASE_DELAY = 0.6
JITTER = 0.4

# State file for resume support
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_state.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_fresh(cached_item, max_days: int = 30) -> bool:
    """True if the item was scraped within max_days."""
    if not cached_item or "error" in cached_item:
        return False
    ts = (cached_item.get("meta", {}).get("timestamp") or
          cached_item.get("meta", {}).get("cache_date", ""))
    if not ts:
        return False
    try:
        last_date = datetime.fromisoformat(ts.split("T")[0])
        return (datetime.now() - last_date).days < max_days
    except Exception:
        return True  # Unparseable timestamp → assume fresh to avoid re-scrape


def _scrape_one(scraper, db, item_id: str, counters: dict) -> str:
    """
    Scrape a single minifig.  Returns: 'cached' | 'scraped' | 'error'.
    Updates counters in-place.
    """
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


def _status_line(item_id, counters, extra=""):
    sys.stdout.write(
        f"\r  {item_id:<14} | "
        f"💾 {counters['cached']}  🌐 {counters['scraped']}  ❌ {counters['errors']}  {extra}   "
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
# Strategy 1: Catalog Discovery (with pagination)
# ---------------------------------------------------------------------------

import random  # needed for jitter — import after stdlib section for clarity


def discover_categories(driver) -> dict:
    """
    Fetch BrickLink catalog tree and return {cat_id: category_name}.
    """
    print("\n🔍  Discovering minifig categories from BrickLink catalog tree...")
    url = "https://www.bricklink.com/catalogTree.asp?itemType=M"
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    categories = {}
    for link in soup.find_all("a", href=re.compile(r"catID=\d+")):
        m = re.search(r"catID=(\d+)", link.get("href", ""))
        if m:
            cat_id = m.group(1)
            name = link.get_text(strip=True)
            if name:
                categories[cat_id] = name

    print(f"  Found {len(categories)} categories.")
    return categories


def get_category_items(driver, cat_id: str, cat_name: str) -> list:
    """
    Scrape ALL pages of a category listing, return list of item IDs.
    Handles BrickLink pagination: ?pg=1, ?pg=2, ...
    """
    item_ids = []
    page = 1
    while True:
        url = (f"https://www.bricklink.com/catalogList.asp"
               f"?catType=M&catID={cat_id}&pg={page}")
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Item links look like href="...?M=sw0001" or "catalogitem.page?M=..."
            found_on_page = []
            for link in soup.find_all("a", href=re.compile(r"[?&]M=")):
                href = link.get("href", "")
                m = re.search(r"[?&]M=([A-Za-z0-9\-]+)", href)
                if m:
                    mid = m.group(1)
                    if mid not in item_ids:
                        found_on_page.append(mid)

            if not found_on_page:
                break  # No more items on this page → done

            item_ids.extend(found_on_page)
            print(f"      Page {page}: +{len(found_on_page)} items  (total so far: {len(item_ids)})")

            # Check if there is a "next page" link before fetching it
            next_link = soup.find("a", string=re.compile(r"Next", re.I))
            if not next_link:
                # Also check for numeric page link higher than current page
                has_next = any(
                    re.search(rf"pg={page+1}", a.get("href", ""))
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


def run_catalog_phase(scraper, db, state: dict, counters_total: dict):
    """Phase 1: catalog-discovery scan."""
    print("\n" + "=" * 70)
    print("PHASE 1 — CATALOG DISCOVERY")
    print("=" * 70)

    driver = scraper._init_driver()
    categories = discover_categories(driver)

    if not categories:
        print("  ❌ No categories found. Skipping catalog phase.")
        return

    already_done_cats = set(state.get("completed_categories", []))
    all_discovered_ids = set(state.get("discovered_ids", []))

    for cat_id, cat_name in sorted(categories.items(), key=lambda x: x[1]):
        if cat_id in already_done_cats:
            print(f"  ⏭️   {cat_name} (already done)")
            continue

        print(f"\n  📦  {cat_name} (cat_id={cat_id})")
        item_ids = get_category_items(driver, cat_id, cat_name)
        new_ids = [i for i in item_ids if i not in all_discovered_ids]
        print(f"      {len(item_ids)} items found, {len(new_ids)} new")

        counters = {"cached": 0, "scraped": 0, "errors": 0}
        for item_id in new_ids:
            _status_line(item_id, counters)
            result = _scrape_one(scraper, db, item_id, counters)
            if result == "scraped":
                name = (db.get_item(item_id) or {}).get("meta", {}).get("item_name", "?")
                print(f"\n    ✨  {item_id} — {name}")
            all_discovered_ids.add(item_id)

        print(f"\n      Summary: 💾 {counters['cached']}  🌐 {counters['scraped']}  ❌ {counters['errors']}")
        for k in counters_total:
            counters_total[k] += counters[k]

        already_done_cats.add(cat_id)
        state["completed_categories"] = list(already_done_cats)
        state["discovered_ids"] = list(all_discovered_ids)
        _save_state(state)

    print("\n✅  Catalog phase complete.")


# ---------------------------------------------------------------------------
# Strategy 2: Prefix-Range Scan
# ---------------------------------------------------------------------------

def run_prefix_phase(scraper, db, state: dict, counters_total: dict):
    """Phase 2: numeric prefix-range scan."""
    print("\n" + "=" * 70)
    print("PHASE 2 — PREFIX-RANGE SCAN")
    print("=" * 70)
    print(f"  {len(PREFIX_RANGES)} prefixes configured\n")

    completed_prefixes = set(state.get("completed_prefixes", []))
    prefix_position = state.get("prefix_position", {})  # {prefix: last_num}

    for prefix, (start, end) in PREFIX_RANGES.items():
        if prefix in completed_prefixes:
            print(f"  ⏭️   {prefix.upper()} (already done)")
            continue

        resume_at = prefix_position.get(prefix, start)
        print(f"\n  🎨  {prefix.upper()}  (#{resume_at}–{end})")

        counters = {"cached": 0, "scraped": 0, "errors": 0}
        consecutive_failures = 0
        num = resume_at

        while num <= end:
            item_id = f"{prefix}{num:04d}"
            _status_line(item_id, counters, f"[{num}/{end}]")

            result = _scrape_one(scraper, db, item_id, counters)

            if result == "error":
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    print(f"\n    ⚠️   {MAX_CONSECUTIVE_FAILURES} consecutive failures — skipping {SKIP_AHEAD} IDs")
                    num += SKIP_AHEAD
                    consecutive_failures = 0
                    continue
            else:
                consecutive_failures = 0
                if result == "scraped":
                    name = (db.get_item(item_id) or {}).get("meta", {}).get("item_name", "?")
                    print(f"\n    ✨  {item_id} — {name}")

            num += 1

            # Checkpoint every 200 items
            if num % 200 == 0:
                prefix_position[prefix] = num
                state["prefix_position"] = prefix_position
                _save_state(state)

        print(f"\n      Summary: 💾 {counters['cached']}  🌐 {counters['scraped']}  ❌ {counters['errors']}")
        for k in counters_total:
            counters_total[k] += counters[k]

        completed_prefixes.add(prefix)
        state["completed_prefixes"] = list(completed_prefixes)
        if prefix in prefix_position:
            del prefix_position[prefix]
        state["prefix_position"] = prefix_position
        _save_state(state)

    print("\n✅  Prefix-range phase complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Comprehensive LEGO minifig scraper")
    parser.add_argument("--catalog-only", action="store_true",
                        help="Only run catalog discovery phase")
    parser.add_argument("--prefix-only", action="store_true",
                        help="Only run prefix-range phase")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from saved state (default: start fresh)")
    parser.add_argument("--clear-state", action="store_true",
                        help="Delete saved state and start fresh")
    args = parser.parse_args()

    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 70)
    print("  COMPREHENSIVE LEGO MINIFIGURE SCRAPER")
    print("=" * 70)
    print(f"  Strategies: {'Catalog' if not args.prefix_only else ''}"
          f"{'/' if not args.catalog_only and not args.prefix_only else ''}"
          f"{'Prefix-range' if not args.catalog_only else ''}")
    print(f"  Cache freshness: 30 days")
    print(f"  Request delay:   {BASE_DELAY}–{BASE_DELAY+JITTER:.1f}s")
    print(f"  Gap detection:   skip {SKIP_AHEAD} after {MAX_CONSECUTIVE_FAILURES} failures")

    if args.clear_state and os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print("\n  🗑️   State file cleared.")

    state = _load_state() if args.resume else {}
    if state:
        print(f"\n  ▶️   Resuming from saved state "
              f"({len(state.get('completed_categories', []))} cats done, "
              f"{len(state.get('completed_prefixes', []))} prefixes done)")

    print("\n  Press ENTER to start (Ctrl+C to stop and save progress)...")
    input()

    db = Database()
    scraper = BrickLinkScraper()
    counters_total = {"cached": 0, "scraped": 0, "errors": 0}
    start_time = time.time()

    try:
        if not args.prefix_only:
            run_catalog_phase(scraper, db, state, counters_total)

        if not args.catalog_only:
            run_prefix_phase(scraper, db, state, counters_total)

    except KeyboardInterrupt:
        print("\n\n  🛑  Scan interrupted — progress saved to scan_state.json")
        print("     Re-run with --resume to continue from where you left off.")
    finally:
        scraper.close()
        db.close()
        elapsed = time.time() - start_time
        total = counters_total["cached"] + counters_total["scraped"]

        print("\n\n" + "=" * 70)
        print("  SCAN SUMMARY")
        print("=" * 70)
        print(f"  ⏱️   Time:    {elapsed/60:.1f} min  ({elapsed/3600:.2f} h)")
        print(f"  💾  Cached:  {counters_total['cached']:,}")
        print(f"  🌐  Scraped: {counters_total['scraped']:,}")
        print(f"  ❌  Errors:  {counters_total['errors']:,}")
        print(f"  📦  Total:   {total:,} minifigures")
        print("=" * 70)

        if counters_total["scraped"] > 0:
            print(f"\n  ✅  {counters_total['scraped']:,} new minifigures added to database!")
        print("  💡  View results in the category pages on the dashboard.\n")

        if os.path.exists(STATE_FILE) and not state.get("completed_prefixes"):
            # If nothing left to do, clean up state file
            try:
                done_cats = len(state.get("completed_categories", []))
                done_pfx = len(state.get("completed_prefixes", []))
                if done_pfx == len(PREFIX_RANGES):
                    os.remove(STATE_FILE)
                    print("  🗑️   State file cleaned up (scan fully complete).")
            except Exception:
                pass


if __name__ == "__main__":
    main()
