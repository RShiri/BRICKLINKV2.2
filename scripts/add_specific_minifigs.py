"""
Quick script to add sh0232, sh0405, and sh0175 to Ram's Collection
"""
from database import Database

db = Database()

minifigs_to_add = ["sh0232", "sh0405", "sh0175"]

print("Adding minifigs to Ram's Collection...")

for fig_id in minifigs_to_add:
    # Check if it exists in items table
    db.cursor.execute("SELECT item_id FROM items WHERE LOWER(item_id) = LOWER(%s)", (fig_id,))
    if db.cursor.fetchone():
        db.add_to_collection(fig_id, "Ram's Collection")
        print(f"  OK - Added: {fig_id}")
    else:
        print(f"  SKIP - {fig_id}: Not in items table (needs to be scraped first)")

print("\nDone! Restart your Streamlit app to see the changes.")

db.close()
