import sqlite3

def check_schema():
    conn = sqlite3.connect('bricklink_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in bricklink_data.db:")
    for table in tables:
        print(f"\n- Table: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]});")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    conn.close()

if __name__ == "__main__":
    check_schema()
