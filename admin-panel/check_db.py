import psycopg2
from config.settings import DB_PARAMS

try:
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users');")
    exists = cur.fetchone()[0]
    print(f"USERS_TABLE_EXISTS: {exists}")
    
    if exists:
        cur.execute("SELECT id, email, status FROM users LIMIT 5;")
        users = cur.fetchall()
        print(f"SAMPLE_USERS: {users}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
