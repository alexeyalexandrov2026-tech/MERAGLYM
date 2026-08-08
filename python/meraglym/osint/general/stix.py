import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class StixAdapter(BaseAdapter):
    """
    Adapter for processing STIX 2.1 Threat Intelligence Data (e.g. from MITRE CTI).
    Maps STIX SDOs (Domain Objects) into MERAGLYM's canonical Entities and Events.
    """
    identifier = "stix_ingest"
    region = "GLOBAL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        stix_objects = payload.get("objects", [])
        if not isinstance(stix_objects, list):
            raise ValueError("STIX adapter payload 'objects' must be a list.")
        if not stix_objects:
            raise ValueError("STIX adapter payload must contain 'objects' array.")

        observations = []
        
        # STIX parsing and Entity mapping
        for obj in stix_objects:
            if not isinstance(obj, dict):
                continue
                
            try:
                stix_type = obj.get("type")
                if not stix_type:
                    continue
                    
                if stix_type == "threat-actor":
                    name = obj.get("name")
                    if not name:
                        continue
                        
                    observations.append({
                        "source_identifier": self.identifier,
                        "region": self.region,
                        "entity_type": "ThreatActor",
                        "entity_value": name,
                        "metadata": {
                            "stix_id": obj.get("id"),
                            "description": str(obj.get("description", "")),
                            "aliases": obj.get("aliases", []) if isinstance(obj.get("aliases"), list) else []
                        },
                        "confidence": 0.90
                    })
                elif stix_type == "campaign":
                    observations.append({
                        "source_identifier": self.identifier,
                        "region": self.region,
                        "entity_type": "Campaign",
                        "entity_value": obj.get("name"),
                        "metadata": {
                            "stix_id": obj.get("id")
                        },
                        "confidence": 0.85
                    })
            except Exception as e:
                # Log or handle parsing exception gracefully
                print(f"Error parsing STIX object: {e}")
                continue

        return observations

registry.register(StixAdapter)
