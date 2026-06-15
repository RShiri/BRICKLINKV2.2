import sys
import os
import sqlite3
import toml
import psycopg2

def sync_cloud_to_local():
    """Syncs all data from PostgreSQL (Supabase) to a local SQLite backup file."""

    secrets_path = os.path.join(os.path.dirname(__file__), '..', '.streamlit', 'secrets.toml')
    if not os.path.exists(secrets_path):
        print("ERROR: .streamlit/secrets.toml not found. Cannot connect to Supabase.")
        sys.exit(1)

    with open(secrets_path) as f:
        secrets = toml.load(f)

    db_config = secrets["supabase"]
    print("Connecting to Supabase...")
    pg_conn = psycopg2.connect(
        host=db_config["host"],
        port=db_config["port"],
        dbname=db_config["dbname"],
        user=db_config["user"],
        password=db_config["password"]
    )
    pg_cursor = pg_conn.cursor()

    local_db_path = os.path.join(os.path.dirname(__file__), '..', 'bricklink_data.db')
    print(f"Writing to local SQLite: {local_db_path}")
    local_conn = sqlite3.connect(local_db_path)
    local_cursor = local_conn.cursor()

    local_cursor.executescript('''
        CREATE TABLE IF NOT EXISTS items (
            item_id TEXT PRIMARY KEY, json_data TEXT, updated_at TEXT,
            cached_rating TEXT, cached_profit REAL, cached_margin REAL
        );
        CREATE TABLE IF NOT EXISTS inventory_lists (
            set_id TEXT PRIMARY KEY, json_data TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS collections (
            item_id TEXT, collection_name TEXT, added_at TEXT,
            PRIMARY KEY (item_id, collection_name)
        );
    ''')

    print("Syncing items...")
    pg_cursor.execute("SELECT item_id, json_data, updated_at, cached_rating, cached_profit, cached_margin FROM items")
    items = pg_cursor.fetchall()
    for row in items:
        local_cursor.execute('''
            INSERT INTO items VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET
                json_data=excluded.json_data, updated_at=excluded.updated_at,
                cached_rating=excluded.cached_rating, cached_profit=excluded.cached_profit,
                cached_margin=excluded.cached_margin
        ''', (row[0], row[1], str(row[2]), row[3], row[4], row[5]))

    print("Syncing inventory_lists...")
    pg_cursor.execute("SELECT set_id, json_data, updated_at FROM inventory_lists")
    invs = pg_cursor.fetchall()
    for row in invs:
        local_cursor.execute('''
            INSERT INTO inventory_lists VALUES (?, ?, ?)
            ON CONFLICT(set_id) DO UPDATE SET json_data=excluded.json_data, updated_at=excluded.updated_at
        ''', (row[0], row[1], str(row[2])))

    print("Syncing collections...")
    pg_cursor.execute("SELECT item_id, collection_name, added_at FROM collections")
    cols = pg_cursor.fetchall()
    for row in cols:
        local_cursor.execute('''
            INSERT INTO collections VALUES (?, ?, ?)
            ON CONFLICT(item_id, collection_name) DO NOTHING
        ''', (row[0], row[1], str(row[2])))

    local_conn.commit()
    local_conn.close()
    pg_cursor.close()
    pg_conn.close()

    print(f"Done. Synced {len(items)} items, {len(invs)} inventories, {len(cols)} collection entries.")

if __name__ == '__main__':
    sync_cloud_to_local()
