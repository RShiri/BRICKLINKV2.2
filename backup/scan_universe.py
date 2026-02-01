import time
import logging
import sys
import random
from datetime import datetime
from scraper import BrickLinkScraper
from database import Database

# Configure execution environment
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format='%(message)s')

def main():
    print("🌍 STARTING UNIVERSAL LEGO SCANNER (2005 - 2026)")
    print("==================================================")
    print("Mode: Year-Based Discovery")
    
    db = Database()
    scraper = BrickLinkScraper()
    
    START_YEAR = 2005
    END_YEAR = 2026
    
    grand_total_scanned = 0
    grand_total_cached = 0
    grand_total_errors = 0
    
    try:
        for year in range(START_YEAR, END_YEAR + 1):
            print(f"\n📅 DISCOVERING ITEMS FOR YEAR: {year}")
            print(f"----------------------------------------")
            
            # Step 1: Discover IDs
            print(f"   Searching catalog...")
            ids = scraper.get_ids_by_year(year)
            
            if not ids:
                print(f"   ⚠️ No items found for {year} (or extraction failed). Skipping.")
                continue
                
            total_items = len(ids)
            print(f"   🔍 Found {total_items} items to scan.")
            
            # Step 2: Scan IDs
            year_scanned = 0
            year_cached = 0
            
            for i, item_id in enumerate(ids):
                # Progress
                progress = (i + 1) / total_items * 100
                sys.stdout.write(f"\r   [{year}] Item {i+1}/{total_items} ({progress:.1f}%) | {item_id}...")
                sys.stdout.flush()
                
                # Check DB first
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
                    year_cached += 1
                    grand_total_cached += 1
                else:
                    try:
                        # Scan
                        data = scraper.scrape(item_id, item_type='M', force=False)
                        if "error" in data:
                            grand_total_errors += 1
                        else:
                            year_scanned += 1
                            grand_total_scanned += 1
                            # Optional: Print cool find
                            # name = data.get('meta', {}).get('item_name', 'Unknown')
                            # print(f"\n      ✨ Found: {name}")
                    except Exception as e:
                        grand_total_errors += 1
            
            print(f"\n   ✅ Year {year} Complete: {year_scanned} New | {year_cached} Cached")
            
            # Save progress / sleep between years
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\n🛑 Scan paused by user.")
        
    finally:
        db.close()
        print(f"\n==================================================")
        print(f"🏁 UNIVERSAL SCAN STOPPED")
        print(f"📦 Total Scraped: {grand_total_scanned}")
        print(f"✅ Total Cached : {grand_total_cached}")
        print(f"❌ Errors       : {grand_total_errors}")

if __name__ == "__main__":
    main()
