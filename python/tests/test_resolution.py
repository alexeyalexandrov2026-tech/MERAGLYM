import pytest
import json
from meraglym.intelligence.resolution import EntityResolutionEngine
from tests.test_worker import DummyConnection

class MockCursor:
    def __init__(self):
        self.queries = []
        self.params = []
        self.returns = []
        
    def execute(self, query, params=None):
        self.queries.append(query)
        self.params.append(params)
        
    def fetchone(self):
        if self.returns:
            return self.returns.pop(0)
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class MockDBConnection:
    def __init__(self):
        self.cursor_obj = MockCursor()
        self.committed = False
        
    def cursor(self):
        return self.cursor_obj
        
    def commit(self):
        self.committed = True

def test_resolution_insert_new():
    conn = MockDBConnection()
    # Mock insert returning ID 1
    conn.cursor_obj.returns = [None, (1,)]
    
    engine = EntityResolutionEngine(conn)
    new_id = engine.insert_or_resolve(
        entity_type="Email",
        value="test@example.com",
        metadata={"source": "test"},
        aliases=["t@example.com"]
    )
    
    assert new_id == 1
    assert conn.committed is True
    queries = [q.strip().replace("\n", "").replace("  ", " ") for q in conn.cursor_obj.queries]
    assert "INSERT INTO \"Entity\"" in queries[1]

def test_resolution_resolve_existing():
    conn = MockDBConnection()
    # Mock existing entity with ID 2 and empty aliases
    conn.cursor_obj.returns = [(2, [])]
    
    engine = EntityResolutionEngine(conn)
    existing_id = engine.insert_or_resolve(
        entity_type="Email",
        value="test@example.com",
    )
    
    assert existing_id == 2
    # No commit needed if no aliases are updated
    assert conn.committed is False

def test_resolution_resolve_and_update_aliases():
    conn = MockDBConnection()
    # Mock existing entity with ID 3 and aliases ["old@example.com"]
    conn.cursor_obj.returns = [(3, ["old@example.com"])]
    
    engine = EntityResolutionEngine(conn)
    existing_id = engine.insert_or_resolve(
        entity_type="Email",
        value="test@example.com",
        aliases=["new@example.com", "old@example.com"]
    )
    
    assert existing_id == 3
    assert conn.committed is True
    queries = [q.strip().replace("\n", "").replace("  ", " ") for q in conn.cursor_obj.queries]
    # Verify update alias query was run
    assert "UPDATE \"Entity\"" in queries[1]
    
    # Verify the merged array
    merged_json = conn.cursor_obj.params[1][0]
    merged_list = json.loads(merged_json)
    assert len(merged_list) == 2
    assert "old@example.com" in merged_list
    assert "new@example.com" in merged_list
