import sqlite3
import json
import os
import toml
import streamlit as st
from database import Database
from tqdm import tqdm

def load_secrets():
    """Manually load secrets for the script."""
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            secrets = toml.load(f)
            # Monkeypatch st.secrets
            st.secrets = secrets
            print("Secrets loaded.")
    else:
        print("Secrets file not found!")
        exit(1)

def migrate():
    print("Starting Migration to Supabase...")
    
    # 1. Load Secrets & Connect to Supabase
    load_secrets()
    cloud_db = Database()
    
    # 2. Connect to Local SQLite
    local_db_path = "bricklink_data.db"
    if not os.path.exists(local_db_path):
        print(f"Local database '{local_db_path}' not found.")
        return

    conn = sqlite3.connect(local_db_path)
    cursor = conn.cursor()
    
    # 3. Migrate Items
    print("\nMigrating Items...")
    cursor.execute("SELECT item_id, json_data, updated_at FROM items")
    items = cursor.fetchall()
    for item in tqdm(items):
        item_id, json_data, updated_at = item
        try:
            # Direct insert to bypass checks/overhead
            query = '''
                INSERT INTO items (item_id, json_data, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (item_id) DO UPDATE SET
                    json_data = EXCLUDED.json_data,
                    updated_at = EXCLUDED.updated_at;
            '''
            cloud_db.cursor.execute(query, (item_id, json_data, updated_at))
        except Exception as e:
            print(f"Failed to migrate item {item_id}: {e}")
    cloud_db.conn.commit()
    
    # 4. Migrate Inventory
    print("\nMigrating Inventory Lists...")
    cursor.execute("SELECT set_id, json_data, updated_at FROM inventory_lists")
    invs = cursor.fetchall()
    for inv in tqdm(invs):
        set_id, json_data, updated_at = inv
        try:
            query = '''
                INSERT INTO inventory_lists (set_id, json_data, updated_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (set_id) DO UPDATE SET
                    json_data = EXCLUDED.json_data,
                    updated_at = EXCLUDED.updated_at;
            '''
            cloud_db.cursor.execute(query, (set_id, json_data, updated_at))
        except Exception as e:
            print(f"Failed to migrate inventory {set_id}: {e}")
    cloud_db.conn.commit()

    # 5. Migrate Collections
    print("\nMigrating Collections...")
    cursor.execute("SELECT item_id, collection_name, added_at FROM collections")
    cols = cursor.fetchall()
    for col in tqdm(cols):
        item_id, col_name, added_at = col
        try:
            query = '''
                INSERT INTO collections (item_id, collection_name, added_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (item_id, collection_name) DO NOTHING;
            '''
            cloud_db.cursor.execute(query, (item_id, col_name, added_at))
        except Exception as e:
            print(f"Failed to migrate collection {item_id}: {e}")
    cloud_db.conn.commit()
    
    print("\nMigration Complete!")
    conn.close()
    cloud_db.close()

if __name__ == "__main__":
    migrate()
