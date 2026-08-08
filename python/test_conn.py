import psycopg
from meraglym.db.session import get_db_connection

try:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            print("Connected successfully:", cur.fetchone())
except Exception as e:
    print("Error:", e)
