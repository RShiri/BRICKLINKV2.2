from database import Database

db = Database()

# Get all sh items
items = db.get_items_by_prefix("sh")

# Filter for the specific IDs we're looking for
target_ids = ["sh0321", "sh0414", "sh0280", "sh0230", "sh0504", "sh0576", "sh0896", "sh0733", "sh0507",
              "sh321", "sh414", "sh280", "sh230", "sh504", "sh576", "sh896", "sh733", "sh507"]

print("Looking for big figure IDs in database...")
print("=" * 60)

found_ids = []
for item in items:
    if "error" in item:
        continue
    
    meta = item.get("meta", {})
    item_id = meta.get("item_id", "")
    item_name = meta.get("item_name", "Unknown")
    
    if item_id in target_ids:
        found_ids.append(item_id)
        print(f"FOUND: {item_id} - {item_name}")

print("=" * 60)
print(f"\nTotal found: {len(found_ids)} out of {len(target_ids)} searched")
print(f"Found IDs: {', '.join(sorted(found_ids))}")

if len(found_ids) < len(target_ids) // 2:
    print("\n⚠️ WARNING: Most IDs not found. They might not be in the database yet.")
else:
    print("\n✓ IDs are in database. Detection logic needs fixing.")

db.close()
