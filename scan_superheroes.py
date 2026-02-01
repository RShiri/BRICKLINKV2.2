import time
import logging
import sys
from datetime import datetime
from scraper import BrickLinkScraper
from database import Database

# Configure concise logging for CLI
logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    # Force UTF-8 for Windows terminals
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("SUPERHERO MINIFIGURE DATABASE SCANNER")
    print("=" * 70)
    print("Scanning BrickLink for all superhero minifigures (sh prefix)")
    print("This will build a comprehensive database of Marvel & DC figures")
    print("-" * 70)
    
    db = Database()
    scraper = BrickLinkScraper()
    
    # CONFIGURATION - Modify these values to change scan range
    START = 1
    END = 1111  # Covers all known superhero minifigs
    
    # Smart gap detection - skip ahead if too many consecutive failures
    MAX_CONSECUTIVE_FAILURES = 50
    SKIP_AHEAD_AMOUNT = 100
    
    total = END - START + 1
    scanned = 0
    cached = 0
    errors = 0
    consecutive_failures = 0
    
    start_time = time.time()
    
    print(f"\n📋 Configuration:")
    print(f"   Range: sh{START:03d} to sh{END:04d}")
    print(f"   Total IDs to check: {total:,}")
    print(f"   Smart Gap Detection: Enabled (skip {SKIP_AHEAD_AMOUNT} after {MAX_CONSECUTIVE_FAILURES} failures)")
    print(f"   Cache Freshness: 30 days")
    print("\n🚀 Starting scan...\n")
    
    try:
        num = START
        while num <= END:
            item_id = f"sh{num:04d}"
            
            # Progress marker
            progress = ((num - START) / total) * 100
            sys.stdout.write(f"\r[{progress:.1f}%] {item_id} | ✅ {cached} | 🌐 {scanned} | ❌ {errors} | ")
            sys.stdout.flush()
            
            # 1. Check DB for existing data
            cached_item = db.get_item(item_id)
            use_cache = False
            
            if cached_item and "error" not in cached_item:
                last_updated = cached_item.get("meta", {}).get("timestamp") or cached_item.get("meta", {}).get("cache_date")
                if last_updated:
                    try:
                        last_date = datetime.fromisoformat(last_updated.split('T')[0])
                        days_diff = (datetime.now() - last_date).days
                        if days_diff < 30:
                            use_cache = True
                    except:
                        use_cache = True

            if use_cache:
                cached += 1
                consecutive_failures = 0  # Reset on success
                sys.stdout.write("💾 Cached")
            else:
                try:
                    # Delay to be nice to BrickLink
                    time.sleep(0.5) 
                    data = scraper.scrape(item_id, item_type='M', force=False)
                    
                    if "error" in data:
                        errors += 1
                        consecutive_failures += 1
                        sys.stdout.write("❌ Not Found")
                        
                        # Smart gap detection
                        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                            print(f"\n\n⚠️  {MAX_CONSECUTIVE_FAILURES} consecutive failures detected!")
                            print(f"   Skipping ahead {SKIP_AHEAD_AMOUNT} IDs to sh{num + SKIP_AHEAD_AMOUNT:04d}...")
                            num += SKIP_AHEAD_AMOUNT
                            consecutive_failures = 0
                            continue
                    else:
                        scanned += 1
                        consecutive_failures = 0  # Reset on success
                        name = data.get('meta', {}).get('item_name', 'Unknown')
                        print(f"\n✨ NEW: {item_id} - {name}")
                        
                except Exception as e:
                    errors += 1
                    consecutive_failures += 1
                    print(f"\n❌ Error {item_id}: {e}")
            
            num += 1

    except KeyboardInterrupt:
        print("\n\n🛑 Scan paused by user.")
    finally:
        scraper.close()  # Close the persistent browser
        db.close()
        elapsed = time.time() - start_time
        
        print("\n\n" + "=" * 70)
        print("🏁 SCAN COMPLETE")
        print("=" * 70)
        print(f"⏱️  Time Elapsed: {elapsed/60:.2f} minutes ({elapsed/3600:.2f} hours)")
        print(f"📦 Total Processed: {num - START:,} IDs")
        print(f"✅ Cached: {cached:,}")
        print(f"🌐 Newly Scraped: {scanned:,}")
        print(f"❌ Errors/Missing: {errors:,}")
        print(f"💾 Database Total: {cached + scanned:,} superhero minifigures")
        print("=" * 70)
        
        if scanned > 0:
            print(f"\n✅ Successfully added {scanned} new minifigures to the database!")
        print(f"\n💡 Tip: Run 'streamlit run dashboard.py' and navigate to 'Superhero Database' to view results")

if __name__ == "__main__":
    main()
