from database import Database

import sys

def check_db():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        
    db = Database()
    print("--- Checking Database for sh001, sh002, sh003 ---")
    
    for item_id in ['sh001', 'sh002', 'sh003']:
        item = db.get_item(item_id)
        if item:
            print(f"✅ FOUND {item_id}: {item.get('meta', {}).get('item_name')}")
        else:
            print(f"❌ MISSING {item_id}")
            
    print("\n--- Checking 'sh' Prefix Fetch ---")
    items = db.get_items_by_prefix("sh")
    print(f"Found {len(items)} items starting with 'sh'")
    for i in items[:5]:
        print(f" - {i.get('meta', {}).get('item_id')}")

if __name__ == "__main__":
    check_db()
