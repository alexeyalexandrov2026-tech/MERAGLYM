from typing import Dict, Any, Optional, Tuple
import json

class EntityResolutionEngine:
    """
    Deterministic and Fuzzy matching engine inspired by OpenCTI and enterprise resolution layers.
    Ensures that before a new entity is inserted by an adapter, it is deduplicated against existing records.
    """
    
    def __init__(self, db_conn):
        self.conn = db_conn

    def resolve_entity(self, entity_type: str, value: str, aliases: list = None) -> Tuple[Optional[int], bool]:
        """
        Attempts to resolve an entity by its type and value.
        If it finds a match, returns (entity_id, True).
        If no match is found, returns (None, False).
        """
        # Step 1: Exact deterministic match (type + value)
        with self.conn.cursor() as cur:
            cur.execute('''
                SELECT id, aliases 
                FROM "Entity" 
                WHERE type = %s AND value = %s
            ''', (entity_type, value))
            row = cur.fetchone()
            
            if row:
                entity_id, existing_aliases = row
                
                # Step 1b: Merge aliases if new ones are provided
                if aliases:
                    existing_aliases_list = existing_aliases if existing_aliases else []
                    merged = list(set(existing_aliases_list + aliases))
                    if len(merged) > len(existing_aliases_list):
                        cur.execute('''
                            UPDATE "Entity" 
                            SET aliases = %s, "updatedAt" = NOW()
                            WHERE id = %s
                        ''', (json.dumps(merged), entity_id))
                        self.conn.commit()
                
                return entity_id, True
            
            # Step 2: Alias-based fuzzy match (if exact value didn't match but an alias does)
            if aliases:
                # In PostgreSQL, we can use JSONB containment or simpler text search for basic aliases.
                # For this implementation, we fall back to a simple LIKE or JSON search if needed,
                # but currently we rely on canonical values primarily.
                pass
                
        return None, False

    def insert_or_resolve(self, entity_type: str, value: str, metadata: dict = None, confidence: float = 1.0, reliability: float = 1.0, aliases: list = None) -> int:
        """
        Main entry point for adapters. Resolves the entity, and if missing, inserts it.
        Returns the canonical Entity ID.
        """
        entity_id, resolved = self.resolve_entity(entity_type, value, aliases)
        if resolved and entity_id:
            return entity_id
            
        # Not found, insert new canonical entity
        with self.conn.cursor() as cur:
            cur.execute('''
                INSERT INTO "Entity" (type, value, metadata, confidence, reliability, aliases, "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                RETURNING id
            ''', (
                entity_type, 
                value, 
                json.dumps(metadata) if metadata else None,
                confidence,
                reliability,
                json.dumps(aliases) if aliases else None
            ))
            new_id = cur.fetchone()[0]
        self.conn.commit()
        return new_id
