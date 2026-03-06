import psycopg2
import streamlit as st
import sys

def test_connection(host, port, user, dbname, password, label):
    print(f"\n--- Testing: {label} ---")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"User: {user}")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            dbname=dbname,
            password=password,
            connect_timeout=5
        )
        print("✅ SUCCESS: Connected!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

if __name__ == "__main__":
    # Get original secrets
    try:
        secrets = st.secrets["supabase"]
        host = secrets["host"]
        port = secrets["port"]
        user = secrets["user"]
        dbname = secrets["dbname"]
        password = secrets["password"]
    except Exception as e:
        print(f"Could not read secrets: {e}")
        sys.exit(1)

    project_ref = user.split('.')[-1] if '.' in user else user
    
    # 1. Original Config
    test_connection(host, port, user, dbname, password, "Original Config")

    # 2. Recommended Pooler Host
    new_host = f"{project_ref}.pooler.supabase.com"
    test_connection(new_host, 6543, user, dbname, password, "New Pooler Host (Port 6543)")

    # 3. Direct Connection (Port 5432) - might be blocked if they have pooling enforced
    direct_host = f"db.{project_ref}.supabase.co"
    test_connection(direct_host, 5432, "postgres", dbname, password, "Direct host (Port 5432)")
