
import sqlite3
import json

def export_to_json(db_path="bricklink_data.db", json_out="bricklink_data.json"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    export = {"items": [], "inventory": [], "collections": []}
    
    # Items
    cursor.execute("SELECT item_id, json_data, updated_at FROM items")
    for r in cursor.fetchall():
        export["items"].append({"id": r[0], "data": r[1], "updated_at": r[2]})
        
    # Inventory
    cursor.execute("SELECT set_id, json_data, updated_at FROM inventory_lists")
    for r in cursor.fetchall():
        export["inventory"].append({"id": r[0], "data": r[1], "updated_at": r[2]})
        
    # Collections
    cursor.execute("SELECT item_id, collection_name, added_at FROM collections")
    for r in cursor.fetchall():
        export["collections"].append({"item_id": r[0], "collection_name": r[1], "added_at": r[2]})
        
    conn.close()
    
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2)
    
    print(f"Exported {len(export['items'])} items to {json_out}")

if __name__ == "__main__":
    export_to_json()
