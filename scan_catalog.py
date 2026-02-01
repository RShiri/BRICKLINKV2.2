import time
import logging
import sys
from datetime import datetime
from scraper import BrickLinkScraper
from database import Database
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

logging.basicConfig(level=logging.INFO, format='%(message)s')

def discover_categories(scraper):
    """Discovers all minifigure categories from BrickLink catalog tree."""
    print("🔍 Discovering minifigure categories from BrickLink...")
    
    driver = scraper._init_driver()
    categories = {}
    
    try:
        # Load catalog tree
        url = "https://www.bricklink.com/catalogTree.asp?itemType=M"
        driver.get(url)
        time.sleep(3)  # Wait for page load
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all category links
        for link in soup.find_all('a', href=re.compile(r'catID=\d+')):
            category_name = link.get_text(strip=True)
            href = link.get('href')
            
            # Extract category ID
            cat_id_match = re.search(r'catID=(\d+)', href)
            if cat_id_match:
                cat_id = cat_id_match.group(1)
                categories[cat_id] = category_name
        
        print(f"✅ Found {len(categories)} categories!")
        for cat_id, name in sorted(categories.items(), key=lambda x: x[1]):
            print(f"   - {name} (ID: {cat_id})")
        
        return categories
        
    except Exception as e:
        print(f"❌ Error discovering categories: {e}")
        return {}

def get_category_items(scraper, cat_id, category_name):
    """Gets all minifigure IDs from a specific category."""
    print(f"\n📦 Fetching items from: {category_name}")
    
    driver = scraper._init_driver()
    item_ids = []
    
    try:
        url = f"https://www.bricklink.com/catalogList.asp?catType=M&catID={cat_id}"
        driver.get(url)
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all minifigure links
        for link in soup.find_all('a', href=re.compile(r'\?M=')):
            href = link.get('href')
            id_match = re.search(r'\?M=([a-zA-Z0-9\-]+)', href)
            if id_match:
                item_id = id_match.group(1)
                if item_id not in item_ids:
                    item_ids.append(item_id)
        
        print(f"   Found {len(item_ids)} items")
        return item_ids
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def main():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 70)
    print("CATALOG-BASED UNIVERSAL MINIFIGURE SCANNER")
    print("=" * 70)
    print("Automatically discovering ALL minifigure themes from BrickLink")
    print("-" * 70)
    
    db = Database()
    scraper = BrickLinkScraper()
    
    # Step 1: Discover all categories
    categories = discover_categories(scraper)
    
    if not categories:
        print("❌ No categories found. Exiting.")
        scraper.close()
        db.close()
        return
    
    print(f"\n📋 Will scan {len(categories)} categories")
    input("\nPress ENTER to start scanning (or Ctrl+C to cancel)...")
    
    total_scanned = 0
    total_cached = 0
    total_errors = 0
    start_time = time.time()
    
    try:
        for cat_id, cat_name in sorted(categories.items(), key=lambda x: x[1]):
            print(f"\n{'='*70}")
            print(f"🎨 CATEGORY: {cat_name}")
            print(f"{'='*70}")
            
            # Get all items in this category
            item_ids = get_category_items(scraper, cat_id, cat_name)
            
            if not item_ids:
                print("   No items found, skipping...")
                continue
            
            scanned = 0
            cached = 0
            errors = 0
            
            for idx, item_id in enumerate(item_ids):
                progress = ((idx + 1) / len(item_ids)) * 100
                sys.stdout.write(f"\r[{progress:.1f}%] {item_id} | ✅ {cached} | 🌐 {scanned} | ❌ {errors} | ")
                sys.stdout.flush()
                
                # Check cache
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
                    sys.stdout.write("💾")
                else:
                    try:
                        time.sleep(0.5)
                        data = scraper.scrape(item_id, item_type='M', force=False)
                        
                        if "error" in data:
                            errors += 1
                            sys.stdout.write("❌")
                        else:
                            scanned += 1
                            name = data.get('meta', {}).get('item_name', 'Unknown')
                            print(f"\n✨ NEW: {item_id} - {name}")
                    except Exception as e:
                        errors += 1
                        sys.stdout.write("❌")
            
            print(f"\n\n📊 {cat_name} Summary:")
            print(f"   Cached: {cached} | Scraped: {scanned} | Errors: {errors}")
            
            total_cached += cached
            total_scanned += scanned
            total_errors += errors
    
    except KeyboardInterrupt:
        print("\n\n🛑 Scan paused by user.")
    finally:
        scraper.close()
        db.close()
        elapsed = time.time() - start_time
        
        print("\n\n" + "=" * 70)
        print("🏁 CATALOG SCAN COMPLETE")
        print("=" * 70)
        print(f"⏱️  Time: {elapsed/60:.2f} minutes ({elapsed/3600:.2f} hours)")
        print(f"✅ Cached: {total_cached:,}")
        print(f"🌐 Scraped: {total_scanned:,}")
        print(f"❌ Errors: {total_errors:,}")
        print(f"💾 Total: {total_cached + total_scanned:,} minifigures")
        print("=" * 70)

if __name__ == "__main__":
    main()
