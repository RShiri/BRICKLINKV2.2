from database import Database
import json

db = Database()

# Check if 76042 is in collection
collection_items = db.get_collection_items("Ram's Collection")
print(f"Is 76042 in collection? {'76042' in collection_items or '76042-1' in collection_items}")

# Get inventory for 76042
db.cursor.execute("SELECT json_data FROM inventory_lists WHERE set_id = %s", ("76042",))
result = db.cursor.fetchone()

if result:
    inv_data = json.loads(result[0])
    print(f"\n76042 has {len(inv_data)} minifigures:")
    
    missing_from_collection = []
    missing_from_items = []
    
    for fig in inv_data:
        fig_id = fig["id"]
        qty = fig.get("quantity", 1)
        print(f"\n  - {fig_id} (qty: {qty})")
        
        # Check if in collection
        if fig_id.lower() in [c.lower() for c in collection_items]:
            print(f"    OK - IN collection")
        else:
            print(f"    MISSING from collection")
            missing_from_collection.append(fig_id)
            
        # Check if in items table
        db.cursor.execute("SELECT item_id FROM items WHERE LOWER(item_id) = LOWER(%s)", (fig_id,))
        item_result = db.cursor.fetchone()
        if item_result:
            print(f"    OK - EXISTS in items table")
        else:
            print(f"    MISSING from items table")
            missing_from_items.append(fig_id)
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total minifigs in 76042: {len(inv_data)}")
    print(f"  Missing from collection: {len(missing_from_collection)}")
    if missing_from_collection:
        print(f"    IDs: {', '.join(missing_from_collection)}")
    print(f"  Missing from items table: {len(missing_from_items)}")
    if missing_from_items:
        print(f"    IDs: {', '.join(missing_from_items)}")
else:
    print("No inventory data for 76042")

db.close()
