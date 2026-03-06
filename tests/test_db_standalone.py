import psycopg2
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
            connect_timeout=10
        )
        print("[SUCCESS] Connected!")
        conn.close()
        return True
    except Exception as e:
        print(f"[FAILED] {e}")
        return False

if __name__ == "__main__":
    # Extracted from .streamlit/secrets.toml
    password = "Rs0526299701"
    dbname = "postgres"
    project_ref = "hskpcqmqjhnbxsgxyvho"
    
    # 1. Original Config from secrets.toml
    test_connection("aws-1-ap-northeast-2.pooler.supabase.com", 6543, f"postgres.{project_ref}", dbname, password, "Original Config")

    # 2. Recommended Pooler Host
    # Supavisor direct pooler
    test_connection(f"{project_ref}.pooler.supabase.com", 6543, f"postgres.{project_ref}", dbname, password, "Recommended Pooler Host (Port 6543)")

    # 3. Direct Connection (Port 5432)
    test_connection(f"db.{project_ref}.supabase.co", 5432, "postgres", dbname, password, "Direct host (Port 5432)")
