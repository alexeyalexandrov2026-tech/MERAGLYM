import time
import json
import traceback
from datetime import datetime, timezone
from pydantic import ValidationError

from meraglym.db.session import get_db_connection
from meraglym.etl.ingest_arf import run_etl

# Import adapters to trigger registry
import meraglym.osint.cis.egrul
import meraglym.osint.general.email
import meraglym.osint.general.stix
import meraglym.osint.cis.rfsd

def process_job(conn, job_id: int, job_type: str, payload: dict, retry_count: int, max_retries: int):
    print(f"Processing job {job_id} of type {job_type} (Attempt {retry_count + 1}/{max_retries + 1})")
    try:
        # Mark as running
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE "Job"
                SET status = 'RUNNING', "startedAt" = %s, "updatedAt" = %s
                WHERE id = %s
            ''', (datetime.now(timezone.utc), datetime.now(timezone.utc), job_id))
        conn.commit()

        if job_type == "ingest_arf":
            source = payload.get("file_path", "https://raw.githubusercontent.com/lockfale/OSINT-Framework/master/public/arf.json")
            if not (source.startswith("http://") or source.startswith("https://")):
                import os
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
            observations = asyncio.run(adapter.execute(payload))
            
            resolution_engine = EntityResolutionEngine(conn)
            resolved_observations = []
            
            for obs in observations:
                entity_id = resolution_engine.insert_or_resolve(
                    entity_type=obs["entity_type"],
                    value=obs["entity_value"],
                    metadata=obs.get("metadata"),
                    confidence=obs.get("confidence", 1.0),
                    reliability=1.0, # Adapter reliability could be pulled from Source
                    aliases=obs.get("metadata", {}).get("aliases", [])
                )
                obs["resolved_entity_id"] = entity_id
                resolved_observations.append(obs)
                
            result = {"status": "success", "observations": resolved_observations}
        else:
            raise ValueError(f"Unknown job type: {job_type}")

        # Mark as completed
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE "Job"
                SET status = 'COMPLETED', result = %s, "completedAt" = %s, "updatedAt" = %s
                WHERE id = %s
            ''', (json.dumps(result), datetime.now(timezone.utc), datetime.now(timezone.utc), job_id))
        conn.commit()
        print(f"Job {job_id} completed successfully.")

    except Exception as e:
        conn.rollback()
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Job {job_id} failed: {e}")
        
        # Decide if we retry or fail permanently
        new_status = 'RETRY' if retry_count < max_retries else 'FAILED'
        
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE "Job"
                SET status = %s, error = %s, "updatedAt" = %s, "retryCount" = "retryCount" + 1
                WHERE id = %s
            ''', (new_status, error_msg, datetime.now(timezone.utc), job_id))
        conn.commit()

def poll_jobs():
    print("Starting ETL job worker...")
    while True:
        try:
            with get_db_connection() as conn:
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
                    
                    if job:
                        job_id, job_type, payload, retry_count, max_retries = job
                        if isinstance(payload, str):
                            payload = json.loads(payload)
                        elif payload is None:
                            payload = {}
                            
                        process_job(conn, job_id, job_type, payload, retry_count, max_retries)
        except Exception as e:
            print(f"Worker polling error: {e}")
            time.sleep(5)
            
        time.sleep(2)

if __name__ == "__main__":
    poll_jobs()
