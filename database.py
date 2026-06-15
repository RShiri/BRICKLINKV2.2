import sqlite3
import json
import os
import logging
import streamlit as st
from datetime import datetime, timedelta

# logging setup
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ============================================================================
# CONNECTION POOLING - Shared local SQLite connection
# ============================================================================
@st.cache_resource
def get_db_pool():
    """
    Creates a single SQLite connection that is cached across all sessions.
    This replaces psycopg2's ThreadedConnectionPool.
    """
    try:
        # Connect to local SQLite DB
        conn = sqlite3.connect('bricklink_data.db', check_same_thread=False, timeout=15)
        # Performance optimizations for SQLite multithreading
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        
        # Initialize tables once
        cursor = conn.cursor()
        _init_tables_once(cursor, conn)
        cursor.close()
        
        logging.info("✅ Local SQLite Database connection initialized")
        return conn
    except Exception as e:
        logging.error(f"❌ Database connection failed: {e}")
        raise e

def reset_db_pool():
    """
    Emergency function to reset the connection pool.
    """
    try:
        get_db_pool.clear()
        logging.warning("⚠️ Connection pool was reset")
        st.toast("Connection pool reset", icon="♻️")
    except Exception as e:
        logging.error(f"Failed to reset pool: {e}")

def _init_tables_once(cursor, conn):
    """Creates the necessary tables if they don't exist."""
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                json_data TEXT,
                updated_at DATETIME
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_lists (
                set_id TEXT PRIMARY KEY,
                json_data TEXT,
                updated_at DATETIME
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                item_id TEXT,
                collection_name TEXT,
                added_at DATETIME,
                PRIMARY KEY (item_id, collection_name)
            );
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL,
                price_new REAL,
                price_used REAL,
                confidence_new TEXT,
                confidence_used TEXT,
                scraped_at DATETIME NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
            );
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_item_id ON price_history(item_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_scraped_at ON price_history(scraped_at);')
        
        try:
            cursor.execute('ALTER TABLE items ADD COLUMN cached_rating TEXT;')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE items ADD COLUMN cached_profit REAL;')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE items ADD COLUMN cached_margin REAL;')
        except sqlite3.OperationalError:
            pass
            
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_cached_rating ON items(cached_rating);')
        
        conn.commit()
        logging.info("✅ Database tables initialized")
    except Exception as e:
        conn.rollback()
        logging.error(f"Table Init Failed: {e}")

class Database:
    """
    Handles SQLite database interactions.
    Manages item data, inventory lists, and collection tracking.
    """

    def __init__(self):
        try:
            self.conn = get_db_pool()
            self.cursor = self.conn.cursor()
        except Exception as e:
            logging.error(f"Database Connection Failed: {e}")
            st.error(f"Database Connection Failed: {e}")
            raise e

    def close(self):
        """
        Closes the cursor. The shared connection remains open for other threads.
        """
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
        except Exception as e:
            logging.error(f"Error closing cursor: {e}")

    def save_item(self, item_id, data):
        if self._is_empty_scrape(data):
            if self.get_item(item_id):
                logging.warning(f"🛡️ Ignoring empty update for {item_id}")
                return

        now = datetime.now().isoformat()
        json_str = json.dumps(data)
        
        try:
            from pricing_engine import PriceAnalyzer
            analysis = PriceAnalyzer(data).analyze()
            rating = analysis.get("deep_dive", {}).get("sniper", {}).get("rating", "N/A")
            profit = analysis.get("deep_dive", {}).get("sniper", {}).get("profit_abs", 0)
            margin = analysis.get("deep_dive", {}).get("sniper", {}).get("margin_pct", 0)
            price_new = analysis.get("new", {}).get("market_price", 0)
            price_used = analysis.get("used", {}).get("market_price", 0)
            conf_new = analysis.get("new", {}).get("confidence", "N/A")
            conf_used = analysis.get("used", {}).get("confidence", "N/A")
        except:
            rating, profit, margin = "N/A", 0, 0
            price_new, price_used = 0, 0
            conf_new, conf_used = "N/A", "N/A"
        
        try:
            query = '''
                INSERT INTO items (item_id, json_data, updated_at, cached_rating, cached_profit, cached_margin)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (item_id) 
                DO UPDATE SET 
                    json_data = excluded.json_data,
                    updated_at = excluded.updated_at,
                    cached_rating = excluded.cached_rating,
                    cached_profit = excluded.cached_profit,
                    cached_margin = excluded.cached_margin;
            '''
            self.cursor.execute(query, (item_id, json_str, now, rating, profit, margin))
            
            history_query = '''
                INSERT INTO price_history (item_id, price_new, price_used, confidence_new, confidence_used, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?);
            '''
            self.cursor.execute(history_query, (item_id, price_new, price_used, conf_new, conf_used, now))
            
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to save item {item_id}: {e}")

    def get_item(self, item_id):
        try:
            self.cursor.execute('SELECT json_data, updated_at FROM items WHERE item_id = ?', (item_id,))
            row = self.cursor.fetchone()
            if row:
                data = json.loads(row[0])
                if "meta" in data:
                    data["meta"]["cache_date"] = str(row[1])
                return data
            return None
        except Exception as e:
            logging.error(f"Get Item Failed: {e}")
            return None

    def save_inventory(self, set_id, data):
        now = datetime.now().isoformat()
        json_str = json.dumps(data)
        try:
            query = '''
                INSERT INTO inventory_lists (set_id, json_data, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT (set_id)
                DO UPDATE SET
                    json_data = excluded.json_data,
                    updated_at = excluded.updated_at;
            '''
            self.cursor.execute(query, (set_id, json_str, now))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Save Inventory Failed: {e}")

    def get_inventory(self, set_id):
        try:
            self.cursor.execute('SELECT json_data, updated_at FROM inventory_lists WHERE set_id = ?', (set_id,))
            row = self.cursor.fetchone()
            if row:
                return json.loads(row[0]), str(row[1])
            return None, None
        except: return None, None

    def add_to_collection(self, item_id, collection_name):
        now = datetime.now().isoformat()
        try:
            query = '''
                INSERT INTO collections (item_id, collection_name, added_at)
                VALUES (?, ?, ?)
                ON CONFLICT (item_id, collection_name) DO NOTHING;
            '''
            self.cursor.execute(query, (item_id, collection_name, now))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Add to Collection Failed: {e}")

    def remove_from_collection(self, item_id, collection_name):
        try:
            self.cursor.execute('DELETE FROM collections WHERE item_id = ? AND collection_name = ?', (item_id, collection_name))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Remove Collection Failed: {e}")

    def get_collection_items(self, collection_name):
        try:
            self.cursor.execute('SELECT item_id FROM collections WHERE collection_name = ?', (collection_name,))
            return [row[0] for row in self.cursor.fetchall()]
        except: return []

    def get_stale_items(self, days_threshold=30):
        try:
            limit_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
            self.cursor.execute('SELECT item_id FROM items WHERE updated_at < ?', (limit_date,))
            return [row[0] for row in self.cursor.fetchall()]
        except: return []

    def _is_empty_scrape(self, data):
        try:
            return (
                not data.get("new", {}).get("sold") and 
                not data.get("new", {}).get("stock") and
                not data.get("used", {}).get("sold") and
                not data.get("used", {}).get("stock")
            )
        except:
            return True

    def get_items_by_prefix(self, prefix):
        try:
            query = "SELECT json_data, updated_at FROM items WHERE item_id LIKE ?"
            self.cursor.execute(query, (prefix + '%',))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                if row[0]:
                    data = json.loads(row[0])
                    if "meta" in data:
                        data["meta"]["cache_date"] = str(row[1])
                    results.append(data)
            return results
        except Exception as e:
            logging.error(f"Get Items By Prefix Failed: {e}")
            return []
    
    def get_price_history(self, item_id, days=30):
        try:
            limit_date = (datetime.now() - timedelta(days=days)).isoformat()
            self.cursor.execute('''
                SELECT price_new, price_used, confidence_new, confidence_used, scraped_at
                FROM price_history
                WHERE item_id = ? AND scraped_at > ?
                ORDER BY scraped_at DESC
            ''', (item_id, limit_date))
            return self.cursor.fetchall()
        except:
            return []
    
    def get_price_trend(self, item_id):
        try:
            history = self.get_price_history(item_id, days=30)
            if len(history) < 2:
                return None
            
            latest = history[0]
            oldest = history[-1]
            
            trend = {}
            if latest[0] and oldest[0]:
                change = ((latest[0] - oldest[0]) / oldest[0]) * 100
                trend['new_change_pct'] = round(change, 1)
            
            if latest[1] and oldest[1]:
                change = ((latest[1] - oldest[1]) / oldest[1]) * 100
                trend['used_change_pct'] = round(change, 1)
            
            return trend
        except:
            return None