import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import Database
from scraper import BrickLinkScraper

def scrape_missing_sh_figures():
    # Force UTF-8 for Windows terminals
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        
    missing_ids = ['sh131', 'sh134', 'sh135', 'sh136', 'sh138', 'sh139', 'sh182', 'sh207', 'sh295', 'sh317', 'sh418', 'sh423', 'sh434', 'sh451', 'sh520', 'sh521', 'sh558', 'sh597', 'sh603', 'sh619']
    missing_ids.extend([f"sh{i:03d}" for i in range(1112, 1150)]) # Let's only do up to 1150 first to avoid too many requests
    
    # We found missing up to 1400, but they might not all exist. Let's start with a smaller batch
    # up to sh1150 to keep it manageable, then evaluate.

    db = Database()
    scraper = BrickLinkScraper()

    print(f"Scraping {len(missing_ids)} missing figures...")
    success = 0
    errors = 0
    scanned = 0
    
    try:
        for item_id in missing_ids:
            sys.stdout.write(f"\rScraping {item_id}... ")
            sys.stdout.flush()
            
            try:
                time.sleep(0.5)
                data = scraper.scrape(item_id, item_type='M', force=False)
                
                if "error" in data:
                    sys.stdout.write("❌ Not Found\n")
                    errors += 1
                else:
                    name = data.get('meta', {}).get('item_name', 'Unknown')
                    sys.stdout.write(f"✅ Success - {name}\n")
                    success += 1
                scanned += 1
            except Exception as e:
                sys.stdout.write(f"❌ Error: {e}\n")
                errors += 1
    except KeyboardInterrupt:
        print("\nAborted.")
    finally:
        scraper.close()
        db.close()
        print(f"\nDone. Saved {success} new items, {errors} errors out of {scanned} scanned.")

if __name__ == '__main__':
    scrape_missing_sh_figures()
