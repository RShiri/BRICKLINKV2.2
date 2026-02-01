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

    print("STARTING MARVEL DATABASE SCANNER (sh001 - sh1111)")
    print("---------------------------------------------------")
    
    db = Database()
    scraper = BrickLinkScraper()
    
    START = 1
    END = 1111
    
    total = END - START + 1
    scanned = 0
    cached = 0
    errors = 0
    
    start_time = time.time()
    
    try:
        for i, num in enumerate(range(START, END + 1)):
            item_id = f"sh{num:03d}"
            
            # Progress marker
            progress = (i + 1) / total * 100
            sys.stdout.write(f"\r[{progress:.1f}%] Checking {item_id}... ")
            sys.stdout.flush()
            
            # 1. Check DB
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
                # sys.stdout.write("✅ Cached\n")
            else:
                try:
                    # Delay to be nice to BrickLink (unless scraping failed immediately)
                    time.sleep(0.5) 
                    data = scraper.scrape(item_id, item_type='M', force=False)
                    if "error" in data:
                        errors += 1
                        sys.stdout.write("❌ Not Found\n")
                    else:
                        scanned += 1
                        print(f"\n✨ NEW DATA: {item_id} - {data.get('meta', {}).get('item_name', 'Unknown')}")
                except Exception as e:
                    errors += 1
                    print(f"\n❌ Error {item_id}: {e}")

    except KeyboardInterrupt:
        print("\n\n🛑 Scan paused by user.")
    finally:
        db.close()
        elapsed = time.time() - start_time
        print(f"\n\n🏁 SCAN COMPLETE")
        print(f"---------------------------------------------------")
        print(f"⏱️ Time: {elapsed/60:.2f} minutes")
        print(f"📦 Total Processed: {total}")
        print(f"✅ Cached: {cached}")
        print(f"🌐 Scraped: {scanned}")
        print(f"❌ Errors/Missing: {errors}")

if __name__ == "__main__":
    main()
