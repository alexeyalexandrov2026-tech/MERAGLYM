import os
import psycopg
import pytest
from pydantic import ValidationError

from meraglym.db.session import get_db_connection
from meraglym.etl.ingest_arf import ArfNode

def test_db_connection():
    # If this fails, the env or DB is not configured correctly
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                assert cur.fetchone()[0] == 1
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")

def test_arf_node_validation():
    # Valid node
    node = ArfNode(name="Test Node", type="folder")
    assert node.name == "Test Node"
    assert node.get_type() == "folder"

    # Auto-infer type
    node_url = ArfNode(name="Test URL", url="https://example.com")
    assert node_url.get_type() == "url"

    node_folder = ArfNode(name="Test Folder", children=[node_url])
    assert node_folder.get_type() == "folder"

    # Invalid node
    with pytest.raises(ValidationError):
        ArfNode(url="https://missing-name.com") # name is required
