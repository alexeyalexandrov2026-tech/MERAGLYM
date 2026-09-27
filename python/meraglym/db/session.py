import os
from contextlib import contextmanager
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, quote
from dotenv import load_dotenv
import psycopg

# Load .env from the project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")
    # Fix psycopg hang on Windows by forcing IPv4
    url = url.replace("localhost", "127.0.0.1")

    # Prisma-style connection strings carry a `?schema=` query parameter, which
    # libpq/psycopg does not understand and rejects with
    # "invalid URI query parameter: schema". Translate it into the standard
    # libpq `options=-c search_path=...` so the same DATABASE_URL works for both
    # the Prisma (Next.js) layer and the Python worker.
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    schema = query.pop("schema", None)
    if schema:
        # Compact libpq form ("-csearch_path=..."); multiple options are
        # space-separated, and urlencode below percent-encodes the space so
        # libpq parses them correctly.
        search_path_opt = f"-csearch_path={schema}"
        existing = query.get("options")
        query["options"] = (
            f"{existing} {search_path_opt}".strip() if existing else search_path_opt
        )
    # quote_via=quote encodes spaces as %20 (not "+"), which libpq requires.
    new_query = urlencode(query, quote_via=quote)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, new_query, parts.fragment)
    )

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
