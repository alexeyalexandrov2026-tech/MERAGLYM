import pytest
from meraglym.intelligence.resolution import EntityResolutionEngine
from unittest.mock import patch

class MockCursor:
    def __init__(self):
        self.query = None
        self.params = None
        self.rows = []
        self.insert_id = 0
        self.execute_count = 0

    def execute(self, query, params=None):
        self.query = query
        self.params = params
        self.execute_count += 1
        
        # Mock behavior for INSERT RETURNING id
        if "INSERT INTO" in query:
            self.insert_id += 1
            self.rows = [(self.insert_id,)]
        # Mock behavior for SELECT
        elif "SELECT" in query:
            # We will just return nothing to simulate db emptiness for new entities
            # Or if we want to simulate the second insert finding the first, we can inject data
            pass
            
    def fetchone(self):
        if self.rows:
            return self.rows.pop(0)
        return None

class MockDBConnection:
    def __init__(self):
        self.cursor_obj = MockCursor()
        self.committed = False
        
    def cursor(self):
        class ContextManager:
            def __init__(self, cur):
                self.cur = cur
            def __enter__(self):
                return self.cur
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return ContextManager(self.cursor_obj)
        
    def commit(self):
        self.committed = True

def test_person_not_merged():
    conn = MockDBConnection()
    
    # We will patch the SELECT to return a match if type and value match
    # But resolution.py should NOT query for exact match on 'Person' just by name!
    engine = EntityResolutionEngine(conn)
    
    # First we inject behavior for SELECT to pretend it found "Иванов Иван Иванович"
    # But only if it actually queries it. If it queries it, it will return (1, None).
    # We want to ensure that it DOES NOT return (1, True) for Person.
    
    # Let's just override resolve_entity inside engine for testing? No, we test resolve_entity itself.
    conn.cursor_obj.rows = [(1, None)] # Mock existing entity ID 1
    
    # Person A
    id_a, resolved_a = engine.resolve_entity("Person", "Иванов Иван Иванович")
    
    # If the engine correctly avoids merging ambiguous Person names, resolved_a should be False
    assert resolved_a is False, "Person entities must not be automatically merged by name alone."

