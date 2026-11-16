import json
import os
import time
import traceback
from datetime import datetime, timezone

import psycopg

from meraglym.db.session import connect
from meraglym.etl.ingest_arf import run_etl

# Importing the package registers every adapter (see meraglym/osint/__init__.py).
import meraglym.osint  # noqa: F401
from meraglym.osint._util import PERMANENT_ERROR_PREFIXES

POLL_INTERVAL = float(os.environ.get("WORKER_POLL_INTERVAL", "2"))
MAX_OBSERVATIONS = int(os.environ.get("WORKER_MAX_OBSERVATIONS", "500"))
ADAPTER_TIMEOUT = float(os.environ.get("WORKER_ADAPTER_TIMEOUT", "1200"))


def _now():
    return datetime.now(timezone.utc)


def _is_permanent(exc: BaseException) -> bool:
    if isinstance(exc, ValueError):
        return True
    return str(exc).startswith(PERMANENT_ERROR_PREFIXES)


def process_job(conn, job_id: int, job_type: str, payload: dict, retry_count: int, max_retries: int):
    print(f"Processing job {job_id} of type {job_type} (Attempt {retry_count + 1}/{max_retries + 1})", flush=True)
    try:
        # Mark as running
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE "Job"
                SET status = 'RUNNING', "startedAt" = %s, "updatedAt" = %s
                WHERE id = %s
            ''', (_now(), _now(), job_id))
        conn.commit()

        if job_type == "ingest_arf":
            source = payload.get("file_path", "https://raw.githubusercontent.com/lockfale/OSINT-Framework/master/public/arf.json")
            if not (source.startswith("http://") or source.startswith("https://")):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                source = os.path.abspath(os.path.join(script_dir, source))
            run_etl(source)
            result = {"status": "success", "message": f"{source} ingested successfully"}
        elif job_type == "run_adapter":
            from meraglym.osint.registry import registry
            from meraglym.intelligence.resolution import EntityResolutionEngine
            import asyncio

            adapter_id = payload.get("adapter_identifier")
            if not adapter_id:
                raise ValueError("run_adapter job requires 'adapter_identifier' in payload.")

            adapter = registry.get_adapter(adapter_id)
            started = time.monotonic()
            observations = asyncio.run(asyncio.wait_for(adapter.execute(payload), ADAPTER_TIMEOUT))
            truncated = len(observations) > MAX_OBSERVATIONS
            observations = observations[:MAX_OBSERVATIONS]

            resolution_engine = EntityResolutionEngine(conn)
            resolved_observations = []

            for obs in observations:
                if not obs.get("entity_value"):
                    continue
                entity_id = resolution_engine.insert_or_resolve(
                    entity_type=obs["entity_type"],
                    value=str(obs["entity_value"]),
                    metadata=obs.get("metadata"),
                    confidence=obs.get("confidence", 1.0),
                    reliability=obs.get("reliability", 1.0),
                    aliases=(obs.get("metadata") or {}).get("aliases", [])
                )
                obs["resolved_entity_id"] = entity_id
                resolved_observations.append(obs)

            result = {
                "status": "success",
                "adapter": adapter_id,
                "count": len(resolved_observations),
                "truncated": truncated,
                "duration_seconds": round(time.monotonic() - started, 1),
                "observations": resolved_observations,
            }
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        # Mark as completed
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE "Job"
                SET status = 'COMPLETED', result = %s, "completedAt" = %s, "updatedAt" = %s
                WHERE id = %s
            ''', (json.dumps(result, default=str), _now(), _now(), job_id))
        conn.commit()
        print(f"Job {job_id} completed successfully.", flush=True)

    except Exception as e:
        conn.rollback()
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Job {job_id} failed: {e}", flush=True)

        # Permanent errors (bad input, missing tool/credential) are not retried.
        if _is_permanent(e):
            new_status = 'FAILED'
            error_msg = str(e)
        else:
            new_status = 'RETRY' if retry_count < max_retries else 'FAILED'

        with conn.cursor() as cur:
            cur.execute('''
                UPDATE "Job"
                SET status = %s, error = %s, "updatedAt" = %s, "retryCount" = "retryCount" + 1
                WHERE id = %s
            ''', (new_status, error_msg, _now(), job_id))
        conn.commit()


def claim_and_process(conn) -> bool:
    """Claim the oldest runnable job (if any) and process it. Returns True if a job ran."""
    with conn.cursor() as cur:
        # Select the oldest pending or retry job
        # Exponential backoff: base 10 seconds * 2^retryCount
        cur.execute('''
            SELECT id, type, payload, "retryCount", "maxRetries"
            FROM "Job"
            WHERE status = 'PENDING'
               OR (status = 'RETRY' AND "updatedAt" < NOW() - (INTERVAL '10 seconds' * POWER(2, "retryCount")))
            ORDER BY "createdAt" ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        ''')
        job = cur.fetchone()
    if not job:
        conn.rollback()  # end the read transaction; do not sit "idle in transaction"
        return False
    job_id, job_type, payload, retry_count, max_retries = job
    if isinstance(payload, str):
        payload = json.loads(payload)
    elif payload is None:
        payload = {}
    process_job(conn, job_id, job_type, payload, retry_count, max_retries)
    return True


def poll_jobs():
    print("Starting ETL job worker...", flush=True)
    conn = None
    backoff = 5
    while True:
        try:
            if conn is None or conn.closed:
                conn = connect()
                print("Database connection established.", flush=True)
                backoff = 5
            if claim_and_process(conn):
                continue  # immediately look for the next job
        except (psycopg.OperationalError, psycopg.InterfaceError) as e:
            print(f"Database connection lost: {e}; reconnecting in {backoff}s", flush=True)
            try:
                if conn is not None:
                    conn.close()
            except Exception:
                pass
            conn = None
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            continue
        except Exception as e:
            print(f"Worker polling error: {e}", flush=True)
            try:
                conn.rollback()
            except Exception:
                conn = None
            time.sleep(5)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    poll_jobs()
