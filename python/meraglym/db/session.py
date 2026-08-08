import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg

# Load .env from the project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    # Fix psycopg hang on Windows by forcing IPv4
    return url.replace("localhost", "127.0.0.1")

@contextmanager
def get_db_connection():
    """
    Context manager to yield a psycopg connection.
    Automatically commits on success, rollbacks on exception.
    """
    url = get_database_url()
    # psycopg 3 connection
    with psycopg.connect(url) as conn:
        yield conn
