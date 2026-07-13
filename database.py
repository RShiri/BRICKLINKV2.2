import psycopg2
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
# CONNECTION POOLING - Thread-safe pool for multi-session support
# ============================================================================
@st.cache_resource
def get_db_pool():
    """
    Creates a ThreadedConnectionPool that is cached across all sessions.
    This allows multiple Database() instances to share connections efficiently.
    Pool size: 10-50 connections (increased to handle high load)
    """
    try:
        from psycopg2 import pool

        db_config = st.secrets["supabase"]
        connection_pool = pool.ThreadedConnectionPool(
            minconn=10,
            maxconn=50,
            host=db_config["host"],
            port=db_config["port"],
            dbname=db_config["dbname"],
            user=db_config["user"],
            password=db_config["password"]
        )

        # Initialize tables once using a connection from the pool
        conn = connection_pool.getconn()
        try:
            cursor = conn.cursor()
            _init_tables_once(cursor, conn)
            cursor.close()
        finally:
            connection_pool.putconn(conn)

        logging.info("✅ Database connection pool initialized (10-50 connections)")
        return connection_pool
    except Exception as e:
        logging.error(f"❌ Database pool creation failed: {e}")
        raise e

def reset_db_pool():
    """
    Emergency function to reset the connection pool.
    Call this if you encounter 'connection pool exhausted' errors.
    """
    try:
        get_db_pool.clear()
        logging.warning("⚠️ Connection pool was reset")
        st.toast("Connection pool reset", icon="♻️")
    except Exception as e:
        logging.error(f"Failed to reset pool: {e}")

def _init_tables_once(cursor, conn):
    """Creates the necessary tables if they don't exist (called once on pool creation)."""
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                json_data TEXT,
                updated_at TIMESTAMPTZ
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_lists (
                set_id TEXT PRIMARY KEY,
                json_data TEXT,
                updated_at TIMESTAMPTZ
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                item_id TEXT,
                collection_name TEXT,
                added_at TIMESTAMPTZ,
                PRIMARY KEY (item_id, collection_name)
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id SERIAL PRIMARY KEY,
                item_id TEXT NOT NULL,
                price_new REAL,
                price_used REAL,
                confidence_new TEXT,
                confidence_used TEXT,
                scraped_at TIMESTAMPTZ NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items(item_id) ON DELETE CASCADE
            );
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_item_id ON price_history(item_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_scraped_at ON price_history(scraped_at);')

        cursor.execute('ALTER TABLE items ADD COLUMN IF NOT EXISTS cached_rating TEXT;')
        cursor.execute('ALTER TABLE items ADD COLUMN IF NOT EXISTS cached_profit REAL;')
        cursor.execute('ALTER TABLE items ADD COLUMN IF NOT EXISTS cached_margin REAL;')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_cached_rating ON items(cached_rating);')

        conn.commit()
        logging.info("✅ Database tables initialized")
    except Exception as e:
        conn.rollback()
        logging.error(f"Table Init Failed: {e}")

class Database:
    """
    Handles PostgreSQL (Supabase) database interactions.
    Manages item data, inventory lists, and collection tracking.

    Uses ThreadedConnectionPool for multi-session support (PC + phone).
    """

    def __init__(self):
        try:
            self.pool = get_db_pool()
            self.conn = self.pool.getconn()

            if self.conn.closed:
                logging.warning("⚠️ Got closed connection from pool, getting new one...")
                self.pool.putconn(self.conn)
                self.conn = self.pool.getconn()

            self.cursor = self.conn.cursor()

        except Exception as e:
            logging.error(f"Database Connection Failed: {e}")
            st.error(f"Database Connection Failed: {e}")
            raise e

    def close(self):
        """
        Closes the cursor and returns the connection to the pool.
        The connection is NOT destroyed, just returned for reuse.
        """
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'conn') and hasattr(self, 'pool'):
                self.pool.putconn(self.conn)
        except Exception as e:
            logging.error(f"Error closing database: {e}")

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
            analysis = None
            rating, profit, margin = "N/A", 0, 0
            price_new, price_used = 0, 0
            conf_new, conf_used = "N/A", "N/A"

        try:
            query = '''
                INSERT INTO items (item_id, json_data, updated_at, cached_rating, cached_profit, cached_margin)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (item_id)
                DO UPDATE SET
                    json_data = EXCLUDED.json_data,
                    updated_at = EXCLUDED.updated_at,
                    cached_rating = EXCLUDED.cached_rating,
                    cached_profit = EXCLUDED.cached_profit,
                    cached_margin = EXCLUDED.cached_margin;
            '''
            self.cursor.execute(query, (item_id, json_str, now, rating, profit, margin))

            # Promoted columns for the web app (migration 0002). Guarded with a
            # savepoint so a database created before that migration keeps working.
            if analysis is not None:
                self.cursor.execute("SAVEPOINT promoted_cols")
                try:
                    from psycopg2.extras import Json
                    from etl.promote import promoted_columns
                    cols = promoted_columns(item_id, data, analysis)
                    self.cursor.execute('''
                        UPDATE items SET
                            item_type = %s, name = %s, year_released = %s,
                            price_new = %s, price_used = %s,
                            confidence_new = %s, confidence_used = %s,
                            buy_target = %s, lifecycle = %s, guide = %s
                        WHERE item_id = %s
                    ''', (cols["item_type"], cols["name"], cols["year_released"],
                          cols["price_new"], cols["price_used"],
                          cols["confidence_new"], cols["confidence_used"],
                          cols["buy_target"], cols["lifecycle"], Json(cols["guide"]),
                          item_id))
                    self.cursor.execute("RELEASE SAVEPOINT promoted_cols")
                except Exception as e:
                    self.cursor.execute("ROLLBACK TO SAVEPOINT promoted_cols")
                    logging.warning(f"Promoted-column update skipped for {item_id}: {e}")

            history_query = '''
                INSERT INTO price_history (item_id, price_new, price_used, confidence_new, confidence_used, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s);
            '''
            self.cursor.execute(history_query, (item_id, price_new, price_used, conf_new, conf_used, now))

            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to save item {item_id}: {e}")

    def get_item(self, item_id):
        try:
            self.cursor.execute('SELECT json_data, updated_at FROM items WHERE item_id = %s', (item_id,))
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
                VALUES (%s, %s, %s)
                ON CONFLICT (set_id)
                DO UPDATE SET
                    json_data = EXCLUDED.json_data,
                    updated_at = EXCLUDED.updated_at;
            '''
            self.cursor.execute(query, (set_id, json_str, now))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Save Inventory Failed: {e}")

    def get_inventory(self, set_id):
        try:
            self.cursor.execute('SELECT json_data, updated_at FROM inventory_lists WHERE set_id = %s', (set_id,))
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
                VALUES (%s, %s, %s)
                ON CONFLICT (item_id, collection_name) DO NOTHING;
            '''
            self.cursor.execute(query, (item_id, collection_name, now))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Add to Collection Failed: {e}")

    def remove_from_collection(self, item_id, collection_name):
        try:
            self.cursor.execute('DELETE FROM collections WHERE item_id = %s AND collection_name = %s', (item_id, collection_name))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Remove Collection Failed: {e}")

    def get_collection_items(self, collection_name):
        try:
            self.cursor.execute('SELECT item_id FROM collections WHERE collection_name = %s', (collection_name,))
            return [row[0] for row in self.cursor.fetchall()]
        except: return []

    def get_stale_items(self, days_threshold=30):
        try:
            limit_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
            self.cursor.execute('SELECT item_id FROM items WHERE updated_at < %s', (limit_date,))
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
            self.cursor.execute("SELECT json_data, updated_at FROM items WHERE item_id LIKE %s", (prefix + '%',))
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
                WHERE item_id = %s AND scraped_at > %s
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
