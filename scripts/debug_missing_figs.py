from database import Database

db = Database()

# Get collection minifigs
collection_items = db.get_collection_items("Ram's Collection")
minifigs = [item for item in collection_items if any(c.isalpha() for c in item)]

print(f"Checking {len(minifigs)} minifigs from collection...")
print(f"Minifigs: {minifigs}\n")

# Check which ones exist in items table
missing = []
exists = []
for fig_id in minifigs:
    db.cursor.execute("SELECT item_id, json_data FROM items WHERE LOWER(item_id) = LOWER(%s)", (fig_id,))
    result = db.cursor.fetchone()
    
    if result:
        exists.append(fig_id)
        print(f"OK {fig_id}: EXISTS in items table")
    else:
        missing.append(fig_id)
        print(f"MISSING {fig_id}: NOT in items table")

print(f"\nSummary:")
print(f"  Exists: {len(exists)}")
print(f"  Missing: {len(missing)}")
if missing:
    print(f"  Missing IDs: {missing}")

db.close()
