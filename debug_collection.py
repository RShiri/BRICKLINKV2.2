from database import Database

db = Database()

# Get all items in Ram's Collection
collection_items = db.get_collection_items("Ram's Collection")
print(f"Total items in Ram's Collection: {len(collection_items)}")

# Count minifigs vs sets
minifigs = [item for item in collection_items if any(c.isalpha() for c in item)]
sets = [item for item in collection_items if not any(c.isalpha() for c in item)]

print(f"Minifigs: {len(minifigs)}")
print(f"Sets: {len(sets)}")

print(f"\nFirst 10 minifigs:")
for fig in minifigs[:10]:
    print(f"  - {fig}")

# Check if these items exist in the items table
print(f"\nChecking if minifigs exist in items table...")
db.cursor.execute("SELECT item_id FROM items WHERE item_id LIKE '%sh%' OR item_id LIKE '%sw%' OR item_id LIKE '%hp%' LIMIT 10")
items_in_db = db.cursor.fetchall()
print(f"Sample items in database: {[row[0] for row in items_in_db]}")

db.close()
