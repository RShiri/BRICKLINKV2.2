import sqlite3
import json
import os
import logging
from datetime import datetime, timedelta

# logging setup
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Database:
    """
    Handles all SQLite database interactions for the BrickLink Scraper.
    Manages item data, inventory lists, and collection tracking.
    """
    DB_NAME = "bricklink_data.db"

    def __init__(self):
        """Initializes the database connection and creates tables if they don't exist."""
        # check_same_thread=False allows sharing connection across threads if needed.
        # timeout=30.0 helps handle concurrent locking by waiting longer before failing.
        self.conn = sqlite3.connect(self.DB_NAME, check_same_thread=False, timeout=30.0)
        self.cursor = self.conn.cursor()
        
        # Concurrency Optimization: WAL Mode
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        self.cursor.execute("PRAGMA synchronous=NORMAL;")
        self.conn.commit()
        
        self._init_tables()

    def _init_tables(self):
        """Creates the necessary tables (items, inventory_lists, collections)."""
        # Table for Items (Sets/Minifigs)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                json_data TEXT,
                updated_at DATETIME
            )
        ''')
        
        # Table for Inventory Lists (Which minifigs are in which set)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_lists (
                set_id TEXT PRIMARY KEY,
                json_data TEXT,
                updated_at DATETIME
            )
        ''')

        # Table for Collections (Separating ownership from data)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                item_id TEXT,
                collection_name TEXT,
                added_at DATETIME,
                PRIMARY KEY (item_id, collection_name)
            )
        ''')
        self.conn.commit()
        
        # Auto-Seed from JSON if DB is empty
        self.cursor.execute("SELECT count(*) FROM items")
        if self.cursor.fetchone()[0] == 0:
            self.seed_from_json("bricklink_data.json")

    def seed_from_json(self, json_path):
        """Seeds the database from a JSON dump file."""
        if not os.path.exists(json_path): return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Seed Items
            for item in data.get('items', []):
                self.cursor.execute(
                    "INSERT OR REPLACE INTO items (item_id, json_data, updated_at) VALUES (?, ?, ?)",
                    (item['id'], item['data'], item['updated_at'])
                )
            
            # Seed Inventory
            for inv in data.get('inventory', []):
                self.cursor.execute(
                    "INSERT OR REPLACE INTO inventory_lists (set_id, json_data, updated_at) VALUES (?, ?, ?)",
                    (inv['id'], inv['data'], inv['updated_at'])
                )
            
            # Seed Collections
            for col in data.get('collections', []):
                self.cursor.execute(
                    "INSERT OR IGNORE INTO collections (item_id, collection_name, added_at) VALUES (?, ?, ?)",
                    (col['item_id'], col['collection_name'], col['added_at'])
                )
            
            self.conn.commit()
            logging.info(f"Seeded database from {json_path}")
        except Exception as e:
            logging.error(f"Failed to seed database: {e}")

    def export_to_json(self, json_path="bricklink_data.json"):
        """Exports the entire database to a JSON file."""
        try:
            export = {"items": [], "inventory": [], "collections": []}
            
            # Items
            self.cursor.execute("SELECT item_id, json_data, updated_at FROM items")
            for r in self.cursor.fetchall():
                export["items"].append({"id": r[0], "data": r[1], "updated_at": r[2]})
                
            # Inventory
            self.cursor.execute("SELECT set_id, json_data, updated_at FROM inventory_lists")
            for r in self.cursor.fetchall():
                export["inventory"].append({"id": r[0], "data": r[1], "updated_at": r[2]})
                
            # Collections
            self.cursor.execute("SELECT item_id, collection_name, added_at FROM collections")
            for r in self.cursor.fetchall():
                export["collections"].append({"item_id": r[0], "collection_name": r[1], "added_at": r[2]})
                
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(export, f, indent=2)
            
            logging.info(f"Exported database to {json_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to export database: {e}")
            return False

    def save_item(self, item_id, data):
        """
        Saves scraped item data to the database.
        
        Args:
            item_id (str): The unique ID of the item.
            data (dict): The dictionary containing scraped data.
        """
        # Anti-Corruption Check: Don't overwrite valid data with empty/bad scrape results
        if self._is_empty_scrape(data):
            existing = self.update_timestamp_if_exists(item_id)
            if existing: 
                # If we have existing data, don't overwrite with empty garbage.
                logging.warning(f"[DB Protection] 🛡️ Ignoring empty data update for {item_id}")
                return

        now = datetime.now().isoformat()
        json_str = json.dumps(data)
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO items (item_id, json_data, updated_at)
                VALUES (?, ?, ?)
            ''', (item_id, json_str, now))
            self.conn.commit()
        except Exception as e:
            logging.error(f"Failed to save item {item_id}: {e}")

    def update_timestamp_if_exists(self, item_id):
        """Checks if item exists and returns it, to avoid unnecessary overwrites."""
        return self.get_item(item_id)

    def _is_empty_scrape(self, data):
        """
        Checks if the scraped data is effectively empty/failed.
        
        Args:
            data (dict): The scrape result.
            
        Returns:
            bool: True if data is empty, False otherwise.
        """
        try:
            return (
                not data.get("new", {}).get("sold") and 
                not data.get("new", {}).get("stock") and
                not data.get("used", {}).get("sold") and
                not data.get("used", {}).get("stock")
            )
        except:
            return True

    def get_item(self, item_id):
        """
        Retrieves an item's data from the database.
        
        Args:
            item_id (str): The Item ID.
            
        Returns:
            dict: The stored data with an injected 'cache_date', or None if not found.
        """
        self.cursor.execute('SELECT json_data, updated_at FROM items WHERE item_id = ?', (item_id,))
        row = self.cursor.fetchone()
        if row:
            data = json.loads(row[0])
            if "meta" in data:
                data["meta"]["cache_date"] = row[1]
            return data
        return None

    def save_inventory(self, set_id, data):
        """Saves the minifigure inventory list for a set."""
        now = datetime.now().isoformat()
        json_str = json.dumps(data)
        self.cursor.execute('''
            INSERT OR REPLACE INTO inventory_lists (set_id, json_data, updated_at)
            VALUES (?, ?, ?)
        ''', (set_id, json_str, now))
        self.conn.commit()

    def get_inventory(self, set_id):
        """Retrieves the minifigure inventory list for a set."""
        self.cursor.execute('SELECT json_data, updated_at FROM inventory_lists WHERE set_id = ?', (set_id,))
        row = self.cursor.fetchone()
        if row:
            return json.loads(row[0]), row[1]
        return None, None

    def add_to_collection(self, item_id, collection_name):
        """Tags an item as part of a specific collection."""
        now = datetime.now().isoformat()
        self.cursor.execute('''
            INSERT OR IGNORE INTO collections (item_id, collection_name, added_at)
            VALUES (?, ?, ?)
        ''', (item_id, collection_name, now))
        self.conn.commit()

    def remove_from_collection(self, item_id, collection_name):
        """Removes an item from a specific collection."""
        self.cursor.execute('''
            DELETE FROM collections WHERE item_id = ? AND collection_name = ?
        ''', (item_id, collection_name))
        self.conn.commit()

    def get_collection_items(self, collection_name):
        """Returns all item IDs in a collection."""
        self.cursor.execute('SELECT item_id FROM collections WHERE collection_name = ?', (collection_name,))
        return [row[0] for row in self.cursor.fetchall()]

    def get_stale_items(self, days_threshold=30):
        """
        Identifies items that haven't been updated in 'days_threshold' days.
        
        Args:
            days_threshold (int): Number of days to consider data stale.
            
        Returns:
            list: List of stale item IDs.
        """
        limit_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
        self.cursor.execute('SELECT item_id FROM items WHERE updated_at < ?', (limit_date,))
        return [row[0] for row in self.cursor.fetchall()]

    def close(self):
        """Closes the database connection."""
        self.conn.close()