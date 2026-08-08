import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import pytest

from meraglym.etl.worker import process_job

class DummyCursor:
    def __init__(self):
        self.queries = []
        self.params = []

    def execute(self, query, params=None):
        self.queries.append(query)
        self.params.append(params)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DummyConnection:
    def __init__(self):
        self.committed = False
        self.rollbacked = False
        self.cursor_obj = DummyCursor()

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rollbacked = True

@patch("meraglym.etl.worker.run_etl")
def test_worker_success(mock_run_etl):
    conn = DummyConnection()
    # PENDING -> RUNNING -> COMPLETED
    process_job(conn, 1, "ingest_arf", {"file_path": "fake.json"}, retry_count=0, max_retries=3)
    
    # Assert run_etl was called
    mock_run_etl.assert_called_once()
    assert "fake.json" in mock_run_etl.call_args[0][0]
    
    # Check queries
    queries = [q.strip().replace(" ", "") for q in conn.cursor_obj.queries]
    
    # query 1: UPDATE to RUNNING
    assert "status='RUNNING'" in queries[0]
    # query 2: UPDATE to COMPLETED
    assert "status='COMPLETED'" in queries[1]
    
    assert conn.committed is True
    assert conn.rollbacked is False

@patch("meraglym.etl.worker.run_etl")
def test_worker_failure_retry(mock_run_etl):
    mock_run_etl.side_effect = Exception("Simulated error")
    conn = DummyConnection()
    
    # PENDING -> RUNNING -> RETRY
    process_job(conn, 2, "ingest_arf", {}, retry_count=0, max_retries=3)
    
    queries = [q.strip().replace(" ", "") for q in conn.cursor_obj.queries]
    
    # query 1: UPDATE to RUNNING
    assert "status='RUNNING'" in queries[0]
    # query 2: UPDATE to RETRY
    assert "status=%s" in queries[1]
    assert conn.cursor_obj.params[1][0] == "RETRY"
    assert "Simulated error" in conn.cursor_obj.params[1][1]
    
    assert conn.rollbacked is True
    assert conn.committed is True

@patch("meraglym.etl.worker.run_etl")
def test_worker_failure_max_retries(mock_run_etl):
    mock_run_etl.side_effect = Exception("Simulated error")
    conn = DummyConnection()
    
    # RETRY -> RUNNING -> FAILED
    process_job(conn, 3, "ingest_arf", {}, retry_count=3, max_retries=3)
    
    queries = [q.strip().replace(" ", "") for q in conn.cursor_obj.queries]
    assert "status=%s" in queries[1]
    assert conn.cursor_obj.params[1][0] == "FAILED"
    
    assert conn.rollbacked is True
