import sys
import os
import sqlite3
import toml
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import Database

def sync_cloud_to_local():
    print("Connecting to cloud Supabase...")
    
    # Need to make sure secrets are loaded
    secrets_path = os.path.join(os.path.dirname(__file__), '..', '.streamlit', 'secrets.toml')
    if os.path.exists(secrets_path):
        with open(secrets_path, "r") as f:
            st.secrets = toml.load(f)
            
    cloud_db = Database()
    
    print("Connecting to local bricklink_data.db...")
    local_db_path = os.path.join(os.path.dirname(__file__), '..', 'bricklink_data.db')
    conn = sqlite3.connect(local_db_path)
    cursor = conn.cursor()
    
    # Sync items
    print("Syncing items...")
    cloud_db.cursor.execute("SELECT item_id, json_data, updated_at FROM items")
    items = cloud_db.cursor.fetchall()
    
    for row in items:
        # SQLite uses DATETIME for updated_at, Supabase uses TIMESTAMPTZ, we'll store as text
        cursor.execute('''
            INSERT INTO items (item_id, json_data, updated_at) 
            VALUES (?, ?, ?)
            ON CONFLICT(item_id) DO UPDATE SET 
            json_data=excluded.json_data, 
            updated_at=excluded.updated_at
        ''', (row[0], row[1], str(row[2])))
        
    # Sync inventory_lists
    print("Syncing inventory_lists...")
    cloud_db.cursor.execute("SELECT set_id, json_data, updated_at FROM inventory_lists")
    invs = cloud_db.cursor.fetchall()
    for row in invs:
        cursor.execute('''
            INSERT INTO inventory_lists (set_id, json_data, updated_at) 
            VALUES (?, ?, ?)
            ON CONFLICT(set_id) DO UPDATE SET 
            json_data=excluded.json_data, 
            updated_at=excluded.updated_at
        ''', (row[0], row[1], str(row[2])))

    # Sync collections
    print("Syncing collections...")
    cloud_db.cursor.execute("SELECT item_id, collection_name, added_at FROM collections")
    cols = cloud_db.cursor.fetchall()
    for row in cols:
        cursor.execute('''
            INSERT INTO collections (item_id, collection_name, added_at) 
            VALUES (?, ?, ?)
            ON CONFLICT(item_id, collection_name) DO NOTHING
        ''', (row[0], row[1], str(row[2])))

    conn.commit()
    conn.close()
    cloud_db.close()
    
    print(f"Sync complete. Local database has {len(items)} items, {len(invs)} inventories, {len(cols)} collection entries.")

if __name__ == '__main__':
    sync_cloud_to_local()
