
import os
import django
import psycopg2

def test_db(url):
    print(f"Testing {url}...")
    try:
        conn = psycopg2.connect(url)
        print(f"  SUCCESS connect to {url}")
        conn.close()
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False

# Try from .env first
db_url_env = "postgres://saleor:saleor@localhost:5435/saleor"
test_db(db_url_env)

# Try default
db_url_def = "postgres://saleor:saleor@localhost:5432/saleor"
test_db(db_url_def)
