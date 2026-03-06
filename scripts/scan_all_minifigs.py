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
    print("UNIVERSAL MINIFIGURE DATABASE SCANNER")
    print("=" * 70)
    print("Scanning ALL LEGO minifigures from all themes")
    print("-" * 70)
    
    db = Database()
    scraper = BrickLinkScraper()
    
    # All known minifigure prefixes with their ranges
    THEMES = {
        "sw": (1, 1500),      # Star Wars
        "hp": (1, 500),       # Harry Potter
        "col": (1, 500),      # Collectible Minifigures
        "lor": (1, 200),      # Lord of the Rings
        "poc": (1, 100),      # Pirates of the Caribbean
        "njo": (1, 800),      # Ninjago
        "cty": (1, 1500),     # City
        "cas": (1, 300),      # Castle
        "tlm": (1, 200),      # The LEGO Movie
        "bat": (1, 300),      # Batman Movie
        "dim": (1, 100),      # Dimensions
        "idea": (1, 100),     # Ideas
        "jw": (1, 100),       # Jurassic World
        "hs": (1, 100),       # Hidden Side
        "twn": (1, 500),      # Town
    }
    
    # Smart gap detection
    MAX_CONSECUTIVE_FAILURES = 50
    SKIP_AHEAD_AMOUNT = 100
    
    total_scanned = 0
    total_cached = 0
    total_errors = 0
    
    start_time = time.time()
    
    print(f"\n📋 Configuration:")
    print(f"   Themes to scan: {len(THEMES)}")
    print(f"   Smart Gap Detection: Enabled")
    print(f"   Cache Freshness: 30 days")
    print("\n🚀 Starting scan...\n")
    
    try:
        for theme_prefix, (start, end) in THEMES.items():
            print(f"\n{'='*70}")
            print(f"🎨 THEME: {theme_prefix.upper()} (Range: {start}-{end})")
            print(f"{'='*70}")
            
            scanned = 0
            cached = 0
            errors = 0
            consecutive_failures = 0
            
            num = start
            while num <= end:
                item_id = f"{theme_prefix}{num:04d}"
                
                # Progress marker
                progress = ((num - start) / (end - start + 1)) * 100
                sys.stdout.write(f"\r[{progress:.1f}%] {item_id} | ✅ {cached} | 🌐 {scanned} | ❌ {errors} | ")
                sys.stdout.flush()
                
                # Check DB for existing data
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
                    consecutive_failures = 0
                    sys.stdout.write("💾")
                else:
                    try:
                        time.sleep(0.5)  # Rate limiting
                        data = scraper.scrape(item_id, item_type='M', force=False)
                        
                        if "error" in data:
                            errors += 1
                            consecutive_failures += 1
                            sys.stdout.write("❌")
                            
                            # Smart gap detection
                            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                                print(f"\n\n⚠️  {MAX_CONSECUTIVE_FAILURES} consecutive failures!")
                                print(f"   Skipping ahead {SKIP_AHEAD_AMOUNT} IDs...")
                                num += SKIP_AHEAD_AMOUNT
                                consecutive_failures = 0
                                continue
                        else:
                            scanned += 1
                            consecutive_failures = 0
                            name = data.get('meta', {}).get('item_name', 'Unknown')
                            print(f"\n✨ NEW: {item_id} - {name}")
                            
                    except Exception as e:
                        errors += 1
                        consecutive_failures += 1
                        sys.stdout.write("❌")
                
                num += 1
            
            # Theme summary
            print(f"\n\n📊 {theme_prefix.upper()} Summary:")
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
        print("🏁 UNIVERSAL SCAN COMPLETE")
        print("=" * 70)
        print(f"⏱️  Time Elapsed: {elapsed/60:.2f} minutes ({elapsed/3600:.2f} hours)")
        print(f"✅ Total Cached: {total_cached:,}")
        print(f"🌐 Total Scraped: {total_scanned:,}")
        print(f"❌ Total Errors: {total_errors:,}")
        print(f"💾 Database Total: {total_cached + total_scanned:,} minifigures")
        print("=" * 70)
        
        if total_scanned > 0:
            print(f"\n✅ Successfully added {total_scanned} new minifigures!")
        print(f"\n💡 Tip: View results in 'All Minifigures' page in dashboard")

if __name__ == "__main__":
    main()
