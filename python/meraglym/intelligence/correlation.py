from typing import List, Dict, Any
from datetime import datetime

class CorrelationEngine:
    """
    Correlation engine inspired by SpiderFoot's post-processing correlation rules.
    This runs after entities and observations are inserted to discover implicit relationships.
    """
    
    def __init__(self, db_conn):
        self.conn = db_conn

    def run_all_rules(self):
        """Execute all correlation rules against the Intelligence Graph."""
        self._correlate_shared_infrastructure()
        self._correlate_temporal_events()

    def _correlate_shared_infrastructure(self):
        """
        Rule: If two different Organizations resolve to or communicate with the same IP/Domain,
        they may have a relationship.
        """
        try:
            with self.conn.cursor() as cur:
                # Find distinct source entities targeting the same target entity (e.g. IP/Domain)
                cur.execute('''
                    WITH SharedTargets AS (
                        SELECT r1."sourceEntityId" AS e1, r2."sourceEntityId" AS e2, r1."targetEntityId" AS target
                        FROM "Relationship" r1
                        JOIN "Relationship" r2 ON r1."targetEntityId" = r2."targetEntityId"
                        WHERE r1."sourceEntityId" != r2."sourceEntityId" 
                          AND r1.type IN ('RESOLVES_TO', 'COMMUNICATES_WITH')
                          AND r2.type IN ('RESOLVES_TO', 'COMMUNICATES_WITH')
                    )
                    INSERT INTO "Relationship" ("sourceEntityId", "targetEntityId", "type", "confidence", "createdAt")
                    SELECT e1, e2, 'SHARED_INFRASTRUCTURE', 0.6, NOW()
                    FROM SharedTargets
                    ON CONFLICT ("sourceEntityId", "targetEntityId", "type") DO NOTHING
                ''')
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error correlating shared infrastructure: {e}")
            
    def _correlate_temporal_events(self):
        """
        Rule: If two distinct entities generate an Observation from the same Source 
        within 5 minutes of each other, tag them as temporally correlated.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute('''
                    WITH TemporalEvents AS (
                        SELECT o1."entityId" AS e1, o2."entityId" AS e2
                        FROM "Observation" o1
                        JOIN "Observation" o2 ON o1."sourceId" = o2."sourceId"
                        WHERE o1."entityId" != o2."entityId"
                          AND ABS(EXTRACT(EPOCH FROM (o1.timestamp - o2.timestamp))) <= 300
                    )
                    INSERT INTO "Relationship" ("sourceEntityId", "targetEntityId", "type", "confidence", "createdAt")
                    SELECT e1, e2, 'TEMPORAL_CORRELATION', 0.4, NOW()
                    FROM TemporalEvents
                    ON CONFLICT ("sourceEntityId", "targetEntityId", "type") DO NOTHING
                ''')
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Error correlating temporal events: {e}")
