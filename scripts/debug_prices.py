from database import Database
import json

db = Database()

# Get a sample item
db.cursor.execute("""
    SELECT item_id, json_data, cached_rating, cached_profit, cached_margin
    FROM items
    LIMIT 5
""")

rows = db.cursor.fetchall()

for row in rows:
    item_id, json_data, cached_rating, cached_profit, cached_margin = row
    print(f"\n{'='*60}")
    print(f"Item ID: {item_id}")
    print(f"Cached Rating: {cached_rating}")
    print(f"Cached Profit: {cached_profit}")
    print(f"Cached Margin: {cached_margin}")
    
    data = json.loads(json_data)
    print(f"\nJSON Structure:")
    print(f"  Keys: {list(data.keys())}")
    
    if 'new' in data:
        print(f"  new keys: {list(data['new'].keys())}")
        print(f"  new.market_price: {data['new'].get('market_price')}")
    
    if 'used' in data:
        print(f"  used keys: {list(data['used'].keys())}")
        print(f"  used.market_price: {data['used'].get('market_price')}")

db.close()
