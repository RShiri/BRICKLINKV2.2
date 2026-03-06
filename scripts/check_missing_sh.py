import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import Database

def find_missing_sh_figures():
    db = Database()
    print("Fetching items with prefix 'sh'...")
    items = db.get_items_by_prefix('sh')
    db.close()
    
    sh_numbers = set()
    for item in items:
        # The structure is usually {'meta': {'item_id': 'sh001', 'item_name': ...}, ...}
        # Or it might be top-level. Let's find it.
        item_id = item.get("meta", {}).get("item_id", "")
        if not item_id and "id" in item.get("meta", {}):
            item_id = item["meta"]["id"]
        
        # sometimes the top level has it depending on schema
        if not item_id and "item_id" in item:
            item_id = item["item_id"]
            
        if item_id.startswith('sh'):
            try:
                num = int(item_id[2:])
                sh_numbers.add(num)
            except ValueError:
                pass
                
    if not sh_numbers:
        print("No SH figures found. Database is empty or error.")
        return
        
    max_num = max(sh_numbers)
    print(f"Database contains {len(sh_numbers)} SH figures. Max found: sh{max_num:03d}")
    
    missing = []
    for i in range(1, 1400):  # Check up to 1400 (just to be safe and cover recent releases)
        if i not in sh_numbers:
            missing.append(i)
            
    print(f"\nMissing IDs between 1 and 1400: {len(missing)}")
    if missing:
        # print gaps
        gaps = []
        start = missing[0]
        prev = missing[0]
        
        for num in missing[1:]:
            if num == prev + 1:
                prev = num
            else:
                gaps.append((start, prev))
                start = num
                prev = num
        gaps.append((start, prev))
        
        print("Gaps:")
        for g_start, g_end in gaps:
            if g_start == g_end:
                print(f"  sh{g_start:03d}")
            else:
                print(f"  sh{g_start:03d} - sh{g_end:03d}")
                
        print("\nAll missing:")
        print([f"sh{m:03d}" for m in missing])

if __name__ == '__main__':
    find_missing_sh_figures()
