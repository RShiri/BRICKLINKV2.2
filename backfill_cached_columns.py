import json
from database import Database
from pricing_engine import PriceAnalyzer
import logging

logging.basicConfig(level=logging.INFO)

def backfill_cached_columns():
    """Backfill cached_rating, cached_profit, cached_margin for existing items."""
    db = Database()
    
    # Get all items with NULL cached columns
    db.cursor.execute("SELECT item_id, json_data FROM items WHERE cached_rating IS NULL")
    rows = db.cursor.fetchall()
    
    total = len(rows)
    logging.info(f"Backfilling {total} items...")
    
    success_count = 0
    error_count = 0
    
    for i, row in enumerate(rows, 1):
        item_id, json_data = row[0], row[1]
        
        try:
            # Specific error handling for corrupted JSON
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                logging.error(f"Corrupted JSON for {item_id}: {e}")
                error_count += 1
                continue
            
            analysis = PriceAnalyzer(data).analyze()
            
            rating = analysis.get("deep_dive", {}).get("sniper", {}).get("rating", "N/A")
            profit = analysis.get("deep_dive", {}).get("sniper", {}).get("profit_abs", 0)
            margin = analysis.get("deep_dive", {}).get("sniper", {}).get("margin_pct", 0)
            
            db.cursor.execute("""
                UPDATE items 
                SET cached_rating = %s, cached_profit = %s, cached_margin = %s
                WHERE item_id = %s
            """, (rating, profit, margin, item_id))
            
            success_count += 1
            if i % 10 == 0:
                db.conn.commit()
                logging.info(f"Progress: {i}/{total} ({i/total*100:.1f}%) | Success: {success_count} | Errors: {error_count}")
                
        except Exception as e:
            logging.error(f"Failed to process {item_id}: {e}")
            error_count += 1
            continue
    
    db.conn.commit()
    db.close()
    
    logging.info(f"Backfill complete: {success_count}/{total} items updated, {error_count} errors")

if __name__ == "__main__":
    backfill_cached_columns()
