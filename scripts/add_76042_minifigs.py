"""
Script to add all minifigs from set 76042 to Ram's Collection
"""
from database import Database
import json

db = Database()

# Get inventory for 76042
db.cursor.execute("SELECT json_data FROM inventory_lists WHERE set_id = %s", ("76042",))
result = db.cursor.fetchone()

if result:
    inv_data = json.loads(result[0])
    print(f"Adding {len(inv_data)} minifigs from 76042 to Ram's Collection...")
    
    added = 0
    for fig in inv_data:
        fig_id = fig["id"]
        
        # Add to collection
        db.add_to_collection(fig_id, "Ram's Collection")
        print(f"  Added: {fig_id}")
        added += 1
    
    print(f"\nDone! Added {added} minifigs to Ram's Collection")
    print(f"Restart your Streamlit app to see the changes.")
else:
    print("No inventory data for 76042")

db.close()
