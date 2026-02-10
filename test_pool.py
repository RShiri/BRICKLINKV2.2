"""
Diagnostic script to check connection pool status
"""
from database import get_db_pool
import time

pool = get_db_pool()

print(f"Connection Pool Status:")
print(f"  Pool object: {pool}")
print(f"  Min connections: {pool.minconn}")
print(f"  Max connections: {pool.maxconn}")

# Try to get connections and see how many we can get
connections = []
try:
    for i in range(55):  # Try to get more than max
        try:
            conn = pool.getconn()
            connections.append(conn)
            print(f"  Got connection #{i+1}")
        except Exception as e:
            print(f"  Failed to get connection #{i+1}: {e}")
            break
    
    print(f"\nTotal connections acquired: {len(connections)}")
    
    # Return all connections
    print(f"\nReturning connections to pool...")
    for i, conn in enumerate(connections):
        pool.putconn(conn)
        print(f"  Returned connection #{i+1}")
    
    print(f"\nAll connections returned successfully!")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    # Clean up
    for conn in connections:
        try:
            pool.putconn(conn)
        except:
            pass
