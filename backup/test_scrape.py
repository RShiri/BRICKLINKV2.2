from scraper import BrickLinkScraper
from database import Database
import sys
import logging

# output to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test():
    print("--- Testing Scrape for sh001 ---")
    scraper = BrickLinkScraper()
    db = Database()
    
    # 1. Scrape
    print("Scraping...")
    data = scraper.scrape("sh001", item_type='M', force=True)
    
    if "error" in data:
        print(f"❌ Scrape Error: {data['error']}")
    else:
        name = data.get("meta", {}).get("item_name", "Unknown")
        print(f"✅ Scrape Success: {name}")
        print(f"   New Sold: {len(data.get('new', {}).get('sold', []))}")
        print(f"   Used Sold: {len(data.get('used', {}).get('sold', []))}")
        
    # 2. Check DB
    print("\n--- Verifying DB Save ---")
    item = db.get_item("sh001")
    if item:
        print("✅ Found in DB")
    else:
        print("❌ NOT Found in DB (Save Failed?)")

if __name__ == "__main__":
    test()
