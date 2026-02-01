import argparse
import sys
import csv
import os
import time
from scraper import BrickLinkScraper
from pricing_engine import PriceAnalyzer

# Force UTF-8 for Windows Consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# --- VISUALS SETUP ---
try:
    from colorama import init, Fore, Style
    from tqdm import tqdm
    init(autoreset=True)
    HAS_VISUALS = True
except ImportError:
    HAS_VISUALS = False
    class MockColor:
        def __getattr__(self, _): return ""
    Fore = Style = MockColor()
    def tqdm(iterable, **kwargs): return iterable
    print("Note: 'colorama' or 'tqdm' not found. Running in plain mode.")

# --- CSV SETUP ---
def init_csvs():
    if not os.path.exists("sets_report.csv"):
        with open("sets_report.csv", "w", newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(["ID", "Name", "Type", "Year", "Status", "Market Price", "Trend", "Minifig Count", "Minifigs Value", "Figs %", "Profit vs Figs", "Rating"])
    
    if not os.path.exists("minifigs_report.csv"):
        with open("minifigs_report.csv", "w", newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(["Parent Set", "Minifig ID", "Name", "Qty", "Cond", "Unit Price", "Total Value"])

def append_set_csv(data):
    with open("sets_report.csv", "a", newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(data)

def append_minifig_csv(data):
    with open("minifigs_report.csv", "a", newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(data)

# --- DISPLAY ---
def print_basic_report(item_id, item_name, results, trend_info=None):
    cache_date = results['meta'].get('cache_date', 'Fresh Fetch')
    
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}BRICKLINK REPORT: {Fore.YELLOW}{item_id} - {item_name}{Style.RESET_ALL}")
    print(f"Last Updated: {cache_date}")
    if trend_info:
        print(f"Trend       : {trend_info}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    
    for condition in ["new", "used"]:
        res = results[condition]
        
        # Color coding confidence
        conf_color = Fore.RED
        if res['confidence'] == "HIGH": conf_color = Fore.GREEN
        elif res['confidence'] == "MEDIUM": conf_color = Fore.YELLOW

        print(f"\n--- {condition.upper()} ---")
        print(f"Market Price   : {Fore.GREEN}{res['market_price']:.2f} ILS{Style.RESET_ALL}")
        print(f"Typical Range  : {res['range'][0]:.2f} - {res['range'][1]:.2f} ILS")
        print(f"Confidence     : {conf_color}{res['confidence']}{Style.RESET_ALL}")
        print(f"Data Integrity : {res['stats']['sold']['final_count']} Sales | {res['stats']['stock']['final_count']} Listings")

def print_deep_dive(results):
    deep = results["deep_dive"]
    lifecycle = deep["lifecycle"]
    sniper = deep["sniper"]
    
    print(f"\n{Fore.CYAN}{'-'*70}{Style.RESET_ALL}")
    print(f"🔍 STEP 2: INVESTMENT ANALYSIS")
    print(f"{Fore.CYAN}{'-'*70}{Style.RESET_ALL}")
    print(f"📅 STATUS: {lifecycle['status']} (Released: {lifecycle['year']})")
    
    print(f"\n🎯 SNIPER OPPORTUNITY (New)")
    if sniper and sniper['rating'] != "NO LISTINGS":
        rating_color = Fore.GREEN if "GOOD" in sniper['rating'] or "EXCELLENT" in sniper['rating'] else Fore.WHITE
        if "IRRELEVANT" in sniper['rating']: rating_color = Fore.RED
        
        print(f"   Deal Rating      : {rating_color}{sniper['rating']}{Style.RESET_ALL}")
        print(f"   Cheapest Listing : {sniper['price']:.2f} ILS")
        print(f"   Potential Profit : {sniper['profit_abs']:.2f} ILS (Margin: {sniper['margin_pct']}%)")
    else:
        print("   No valid listings found.")



# --- PROCESSORS ---

def get_market_price(item_id, item_type, force, mf_new=0.0, mf_used=0.0):
    scraper = BrickLinkScraper()
    raw = scraper.scrape(item_id, item_type=item_type, force=force)
    if "error" in raw: return None, raw
    engine = PriceAnalyzer(raw)
    return engine.analyze(minifig_value_new=mf_new, minifig_value_used=mf_used), raw

def calculate_minifigs(set_id, minifig_list, force, silent=False):
    total_new = 0.0
    total_used = 0.0
    row_data = [] # Store for later printing
    
    cache_checker = BrickLinkScraper()

    if not silent:
        print(f"   🔎 Calculating market values for {len(minifig_list)} figures...\n")
        print(f"   {'ID':<10} {'Name':<35} {'Qty':<5} {'New (ea)':<12} {'Used (ea)':<12}")
        print(f"   {'-'*10} {'-'*35} {'-'*5} {'-'*12} {'-'*12}")

    iterator = tqdm(minifig_list, desc="   ⏳  Analyzing Figures", leave=False) if HAS_VISUALS else minifig_list

    for mf in iterator:
        source_label = "🌐"
        if not force and cache_checker._is_cache_valid(mf['id']):
            source_label = "💾"
        
        # Only print progress if not silent (or let tqdm handle it if enabled)
        # For simplicity, if silent=True, we rely on a global spinner or just silence.
        # But we need values.
        
        try:
           res, _ = get_market_price(mf['id'], 'M', force)
           if res:
               p_new = res['new']['market_price']
               p_used = res['used']['market_price']
               
               line_new = p_new * mf['qty']
               line_used = p_used * mf['qty']
               
               total_new += line_new
               total_used += line_used
               
               # Store data for later
               row_data.append({
                   "id": mf['id'], "name": mf['name'], "qty": mf['qty'],
                   "p_new": p_new, "line_new": line_new,
                   "p_used": p_used, "line_used": line_used,
                   "source": source_label
               })

               if not silent:
                   print(f"\r   {mf['id']:<10} {mf['name'][:35]:<35} {mf['qty']:<5} {p_new:<12.2f} {p_used:<12.2f}")
               
               append_minifig_csv([set_id, mf['id'], mf['name'], mf['qty'], "NEW", f"{p_new:.2f}", f"{line_new:.2f}"])
               append_minifig_csv([set_id, mf['id'], mf['name'], mf['qty'], "USED", f"{p_used:.2f}", f"{line_used:.2f}"])
        except Exception as e:
            if not silent: print(f"\r   ❌ Error fetching {mf['id']}: {e}                     ")

    return total_new, total_used, row_data

def print_minifigs_table(minifig_list, row_data):
    print(f"\n{Fore.CYAN}{'-'*70}{Style.RESET_ALL}")
    print(f"👥 STEP 3: MINIFIGURE BREAKDOWN")
    print(f"{Fore.CYAN}{'-'*70}{Style.RESET_ALL}")
    print(f"   ✅ Found {len(minifig_list)} minifigures.")
    print(f"   {'ID':<10} {'Name':<35} {'Qty':<5} {'New (ea)':<12} {'Used (ea)':<12}")
    print(f"   {'-'*10} {'-'*35} {'-'*5} {'-'*12} {'-'*12}")
    
    for r in row_data:
        print(f"   {r['id']:<10} {r['name'][:35]:<35} {r['qty']:<5} {r['p_new']:<12.2f} {r['p_used']:<12.2f}")

# --- MAIN ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("item_ids", nargs="+", help="List of Item IDs")
    parser.add_argument("--type", default="S", choices=["S", "M"])
    parser.add_argument("--force", action="store_true", help="Ignore cache and force fresh scrape")
    args = parser.parse_args()
    
    init_csvs()
    
    grand_total_new_mkt = 0
    grand_total_used_mkt = 0
    batch_summary = []

    pbar_items = tqdm(args.item_ids, desc="Processing Items", unit="item") if HAS_VISUALS and len(args.item_ids) > 1 else args.item_ids

    for i, current_id in enumerate(pbar_items):
        
        if not HAS_VISUALS and i > 0:
            print(f"\n\n{'#'*80}")
            print(f"{'#'*30}   NEXT ITEM   {'#'*35}")
            print(f"{'#'*80}\n")

        # Auto-detect logic
        itype = "S"
        if args.type.lower() in ["m", "minifig"]: 
            itype = "M"
        elif not current_id[0].isdigit():
            # print(f"   ✨ Auto-detected Minifigure ID for {current_id}. Switching type to 'M'.")
            itype = "M"

        # print(f"Preparing to fetch data for {current_id} ({itype})...")
        
        temp_scraper = BrickLinkScraper()
        
        # --- TREND ANALYSIS SETUP ---
        old_price = 0
        trend_str = ""
        try:
            old_item = temp_scraper.db.get_item(current_id)
            if old_item:
                old_engine = PriceAnalyzer(old_item)
                old_res = old_engine.analyze()
                old_price = old_res['new']['market_price']
        except:
            pass
        
        if not args.force and temp_scraper._is_cache_valid(current_id):
            if not HAS_VISUALS: print(f"   💾 Found data in cache. Loading...")
            pass
        else:
            if not HAS_VISUALS: print(f"   🌐 Data not in cache (or forced). Downloading from BrickLink...")
            pass

        # --- MINIFIGS LOGIC (PRE-CALC) ---
        mf_val_new = 0.0
        mf_val_used = 0.0
        minifig_list = []

        if itype == 'S':
            # print(f"   🔎 Pre-scanning Minifigures (Silent Mode)...")
            
            # Use temp scraper for finding minifigs
            msg_inv = f"   ⏳ Fetching inventory for {current_id}..."
            is_batch = HAS_VISUALS and len(args.item_ids) > 1
            
            if is_batch:
                pbar_items.set_description(f"⏳ Inventory {current_id}")
            else:
                sys.stdout.write(msg_inv)
                sys.stdout.flush()
            
            minifig_list = temp_scraper.get_minifigs_in_set(current_id, args.force)
            
            if is_batch:
                pbar_items.set_description(f"Processing Items")
            else:
                sys.stdout.write("\r" + " "*len(msg_inv) + "\r")
                sys.stdout.flush()
            
            if minifig_list:
                # Calculate silently to get values for pollution filter
                mf_val_new, mf_val_used, mf_details = calculate_minifigs(current_id, minifig_list, args.force, silent=True)
            # else:
            #     print("   🚫 No minifigures found in this set.")

        try:
            # Ephemeral loading message
            msg = f"   ⏳ Fetching data for set {current_id}..."
            is_batch = HAS_VISUALS and len(args.item_ids) > 1

            if is_batch:
                pbar_items.set_description(f"⏳ Price {current_id}")
            else:
                sys.stdout.write(msg)
                sys.stdout.flush()

            # Now pass the calculated logic to the main price engine
            results, raw = get_market_price(current_id, itype, args.force, mf_val_new, mf_val_used)
            
            # Clear the loading message
            if is_batch:
                pbar_items.set_description(f"Processing Items")
            else:
                sys.stdout.write("\r" + " "*len(msg) + "\r")
                sys.stdout.flush()
        except Exception as e:
            print(f"{Fore.RED}Error processing {current_id}: {e}{Style.RESET_ALL}")
            continue
        
        if not results:
            print(f"Error: {raw.get('error', 'Unknown Error')}")
            continue

        # Calculate Trend
        new_price = results['new']['market_price']
        
        # Only show trend if we actually updated the data (Timestamp check)
        is_updated = False
        if old_item:
            old_ts = old_item.get("meta", {}).get("timestamp")
            new_ts = results.get("meta", {}).get("timestamp")
            if old_ts != new_ts:
                is_updated = True

        if is_updated and old_price > 0 and new_price > 0:
            diff = new_price - old_price
            pct = (diff / old_price) * 100
            symbol = "▲" if diff > 0 else "▼"
            color = Fore.GREEN if diff > 0 else Fore.RED
            trend_str = f"{color}{new_price:.2f} ILS {symbol} {abs(pct):.1f}% since last scan{Style.RESET_ALL}"
            
        grand_total_new_mkt += results['new']['market_price']
        grand_total_used_mkt += results['used']['market_price']

        meta = results["meta"]
        # Clear line for clean report if using tqdm
        if HAS_VISUALS and len(args.item_ids) > 1: print("\r" + " "*100 + "\r")
        
        print_basic_report(current_id, meta['item_name'], results, trend_str)
        print_deep_dive(results)
        
        # --- PRINT MINIFIG TABLE (NOW STEP 3) ---
        if itype == 'S' and minifig_list:
            print_minifigs_table(minifig_list, mf_details)
        
        # --- COMPARISON DISPLAY ---
        if itype == 'S' and minifig_list:
            set_price_new = results['new']['market_price']
            set_price_used = results['used']['market_price']
            
            pct_new = (mf_val_new / set_price_new * 100) if set_price_new > 0 else 0
            pct_used = (mf_val_used / set_price_used * 100) if set_price_used > 0 else 0

            print(f"\n{Fore.CYAN}{'-'*70}{Style.RESET_ALL}")
            print(f"📊 COMPARISON (Set vs Minifigs)")
            print(f"{Fore.CYAN}{'-'*70}{Style.RESET_ALL}")
            print(f"   {'Metric':<15} {'NEW':<15} {'USED':<15}")
            print(f"   {'-'*45}")
            print(f"   {'Set Price':<15} {set_price_new:<15.2f} {set_price_used:<15.2f}")
            print(f"   {'Figs Sum':<15} {mf_val_new:<15.2f} {mf_val_used:<15.2f}")
            print(f"   {'Figs % of Set':<15} {pct_new:<14.1f}% {pct_used:<14.1f}%")
            
            if pct_new > 80: 
                print(f"   🔥 NEW: Strong Part-Out Candidate! (Figs > 80% of Set Price)")
            else: 
                print(f"   ❄️ NEW: Value is mostly in the bricks.")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

        # Save CSV
        deep = results["deep_dive"]
        po = results.get("part_out", {})
        
        # Minifig Check (Safe access)
        mf_count = len(minifig_list) if (itype == 'S' and 'minifig_list' in locals() and minifig_list) else 0
        mf_pct = 0.0
        if itype == 'S' and 'pct_new' in locals():
            mf_pct = pct_new

        row = [
            meta.get("item_id"), meta.get("item_name"), itype, meta.get("year_released"),
            deep["lifecycle"]["status"], results["new"]["market_price"],
            trend_str if trend_str else "N/A",
            mf_count,           # New: Minifig Count
            mf_val_new,         # Minifigs Value
            f"{mf_pct:.1f}%",   # New: Figs %
            (mf_val_new - results["new"]["market_price"]), # Profit vs Figs
            deep["sniper"]["rating"]
        ]
        append_set_csv(row)
        
        # Add to Batch Summary
        batch_summary.append({
            "id": current_id,
            "name": meta.get("item_name", "Unknown"),
            "new": results["new"]["market_price"],
            "used": results["used"]["market_price"]
        })
        
        print(f"✅ Data for {current_id} saved to CSV.")

    if len(args.item_ids) > 1:
        print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
        print(f"📊 BATCH SUMMARY")
        print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
        print(f"{'ID':<10} {'Name':<35} {'NEW (ILS)':<12} {'USED (ILS)':<12}")
        print(f"{'-'*10} {'-'*35} {'-'*12} {'-'*12}")
        
        for item in batch_summary:
            p_new = f"{item['new']:.2f}" if item['new'] > 0 else "NONE"
            p_used = f"{item['used']:.2f}" if item['used'] > 0 else "NONE"
            print(f"{item['id']:<10} {item['name'][:35]:<35} {p_new:<12} {p_used:<12}")

        print(f"\n{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")
        print(f"🏆 GRAND TOTALS ({len(args.item_ids)} Items)")
        print(f"{'='*70}")
        print(f"NEW Condition  : {Fore.GREEN}{grand_total_new_mkt:.2f} ILS{Style.RESET_ALL}")
        print(f"USED Condition : {Fore.YELLOW}{grand_total_used_mkt:.2f} ILS{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*70}{Style.RESET_ALL}")

    print("\n🏁 All requested items processed.")

if __name__ == "__main__":
    main()