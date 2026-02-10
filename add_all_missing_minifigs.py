"""
Script to add ALL missing minifigs from ALL sets in Ram's Collection
"""
from database import Database
import json

db = Database()

# Get all sets in collection
collection_items = db.get_collection_items("Ram's Collection")
sets_in_collection = [item for item in collection_items if not any(c.isalpha() for c in item)]

print(f"Found {len(sets_in_collection)} sets in Ram's Collection")
print(f"Checking for missing minifigs...\n")

total_minifigs_to_add = []
sets_with_missing_figs = []

# Check each set
for set_id in sets_in_collection:
    # Get inventory
    db.cursor.execute("SELECT json_data FROM inventory_lists WHERE set_id = %s", (set_id,))
    result = db.cursor.fetchone()
    
    if result:
        inv_data = json.loads(result[0])
        missing_for_this_set = []
        
        for fig in inv_data:
            fig_id = fig["id"]
            
            # Check if minifig is in collection
            if fig_id.lower() not in [c.lower() for c in collection_items]:
                # Check if it exists in items table
                db.cursor.execute("SELECT item_id FROM items WHERE LOWER(item_id) = LOWER(%s)", (fig_id,))
                if db.cursor.fetchone():
                    missing_for_this_set.append(fig_id)
                    total_minifigs_to_add.append(fig_id)
        
        if missing_for_this_set:
            sets_with_missing_figs.append(set_id)
            print(f"Set {set_id}: {len(missing_for_this_set)} missing minifigs")
            for fig_id in missing_for_this_set:
                print(f"  - {fig_id}")

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  Sets with missing minifigs: {len(sets_with_missing_figs)}")
print(f"  Total minifigs to add: {len(total_minifigs_to_add)}")

if total_minifigs_to_add:
    print(f"\nDo you want to add all {len(total_minifigs_to_add)} minifigs to Ram's Collection?")
    response = input("Type 'yes' to proceed: ")
    
    if response.lower() == 'yes':
        print(f"\nAdding minifigs...")
        added = 0
        for fig_id in total_minifigs_to_add:
            db.add_to_collection(fig_id, "Ram's Collection")
            print(f"  Added: {fig_id}")
            added += 1
        
        print(f"\nDone! Added {added} minifigs to Ram's Collection")
        print(f"Restart your Streamlit app to see the changes.")
    else:
        print("Cancelled.")
else:
    print("\nNo missing minifigs found!")

db.close()
