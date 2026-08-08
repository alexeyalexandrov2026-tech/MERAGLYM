import pytest
from meraglym.intelligence.correlation import CorrelationEngine
from tests.test_worker import DummyConnection

def test_correlation_engine_no_exceptions():
    conn = DummyConnection()
    engine = CorrelationEngine(conn)
    
    # Run the correlation rules
    engine.run_all_rules()
    
    assert conn.committed is True
    assert conn.rollbacked is False
    
    queries = [q.strip().replace(" ", "").replace("\n", "") for q in conn.cursor_obj.queries]
    # We should have executed the shared infrastructure and temporal correlation rules
    assert any("SHARED_INFRASTRUCTURE" in q for q in queries)
    assert any("TEMPORAL_CORRELATION" in q for q in queries)
