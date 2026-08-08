import json
import os
import argparse
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ValidationError

from meraglym.db.session import get_db_connection

class ArfNode(BaseModel):
    name: str
    type: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    pricing: Optional[str] = None
    bestFor: Optional[str] = None
    input: Optional[str] = None
    output: Optional[str] = None
    opsec: Optional[str] = None
    opsecNote: Optional[str] = None
    localInstall: Optional[bool] = None
    googleDork: Optional[bool] = None
    registration: Optional[bool] = None
    editUrl: Optional[bool] = None
    api: Optional[bool] = None
    invitationOnly: Optional[bool] = None
    deprecated: Optional[bool] = None
    children: Optional[List["ArfNode"]] = None

    def get_type(self) -> str:
        if self.type:
            return self.type
        return "folder" if self.children else "url"

def run_etl(source: str):
    print(f"Starting ETL process from {source}")
    
    if source.startswith("http://") or source.startswith("https://"):
        import httpx
        print(f"Downloading {source}...")
        response = httpx.get(source)
        response.raise_for_status()
        data = response.json()
    else:
        if not os.path.exists(source):
            raise FileNotFoundError(f"File {source} not found")
        with open(source, "r", encoding="utf-8") as f:
            data = json.load(f)
        
    try:
        if isinstance(data, list):
            roots = [ArfNode(**n) for n in data]
        else:
            roots = [ArfNode(**data)]
    except ValidationError as e:
        print(f"Validation error: {e}")
        raise
        
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # We process level by level to allow batch inserts/updates
            # current_level is a list of tuples: (parent_id, ArfNode)
            current_level: List[Tuple[Optional[int], ArfNode]] = [(None, root) for root in roots]
            
            while current_level:
                # Group nodes by parent_id for efficient querying
                parent_ids = list(set(p_id for p_id, _ in current_level))
                
                # Fetch existing nodes for these parents
                if None in parent_ids:
                    # Root nodes
                    cur.execute('SELECT id, name, "parentId" FROM "Node" WHERE "parentId" IS NULL')
                    existing_roots = cur.fetchall()
                    # Filter out None and query the rest
                    other_parents = [p for p in parent_ids if p is not None]
                    existing_others = []
                    if other_parents:
                        cur.execute('SELECT id, name, "parentId" FROM "Node" WHERE "parentId" = ANY(%s)', (other_parents,))
                        existing_others = cur.fetchall()
                    existing_nodes = existing_roots + existing_others
                else:
                    cur.execute('SELECT id, name, "parentId" FROM "Node" WHERE "parentId" = ANY(%s)', (parent_ids,))
                    existing_nodes = cur.fetchall()
                
                # Map existing nodes by (name, parentId) -> id
                existing_map = {(row[1], row[2]): row[0] for row in existing_nodes}
                
                inserts = []
                updates = []
                
                for parent_id, node in current_level:
                    key = (node.name, parent_id)
                    params = (
                        node.get_type(), node.url, node.description, node.status, node.pricing,
                        node.bestFor, node.input, node.output, node.opsec, node.opsecNote,
                        node.localInstall, node.googleDork, node.registration, node.editUrl,
                        node.api, node.invitationOnly, node.deprecated
                    )
                    
                    if key in existing_map:
                        node_id = existing_map[key]
                        updates.append(params + (node_id,))
                        # We will need the node_id later for children
                        # Python allows adding attributes to objects dynamically but Pydantic BaseModel does not
                        # We will maintain a mapping
                    else:
                        inserts.append((node.name, parent_id) + params + (datetime.now(timezone.utc),))
                
                # Perform bulk updates
                if updates:
                    cur.executemany('''
                        UPDATE "Node"
                        SET type = %s, url = %s, description = %s, status = %s, pricing = %s,
                            "bestFor" = %s, input = %s, output = %s, opsec = %s, "opsecNote" = %s,
                            "localInstall" = %s, "googleDork" = %s, registration = %s, "editUrl" = %s,
                            api = %s, "invitationOnly" = %s, deprecated = %s
                        WHERE id = %s
                    ''', updates)
                
                # Perform bulk inserts and retrieve their IDs
                new_ids_map = {}
                if inserts:
                    cur.executemany('''
                        INSERT INTO "Node" (
                            name, "parentId", type, url, description, status, pricing,
                            "bestFor", input, output, opsec, "opsecNote",
                            "localInstall", "googleDork", registration, "editUrl",
                            api, "invitationOnly", deprecated, "createdAt"
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id, name, "parentId"
                    ''', inserts, returning=True)
                    
                    for row in cur:
                        # row is (id, name, parentId)
                        new_ids_map[(row[1], row[2])] = row[0]
                
                # Prepare next level
                next_level = []
                for parent_id, node in current_level:
                    if node.children:
                        key = (node.name, parent_id)
                        # The node_id is either in existing_map or new_ids_map
                        node_id = existing_map.get(key) or new_ids_map.get(key)
                        for child in node.children:
                            next_level.append((node_id, child))
                            
                current_level = next_level

            # Commit the transaction once the entire tree is processed
            conn.commit()
            
    print("ETL process completed successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest arf.json into PostgreSQL")
    parser.add_argument("--file", default="https://raw.githubusercontent.com/lockfale/OSINT-Framework/master/public/arf.json", help="Path or URL to arf.json")
    args = parser.parse_args()
    
    target = args.file
    if not (target.startswith("http://") or target.startswith("https://")):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target = os.path.abspath(os.path.join(script_dir, args.file))
    
    run_etl(target)
