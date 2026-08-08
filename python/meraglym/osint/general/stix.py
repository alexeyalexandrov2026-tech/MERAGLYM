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
        if not stix_objects:
            raise ValueError("STIX adapter payload must contain 'objects' array.")

        observations = []
        
        # Simulate STIX parsing and Entity mapping
        await asyncio.sleep(0.5)

        for obj in stix_objects:
            stix_type = obj.get("type")
            if stix_type == "threat-actor":
                observations.append({
                    "source_identifier": self.identifier,
                    "region": self.region,
                    "entity_type": "ThreatActor",
                    "entity_value": obj.get("name"),
                    "metadata": {
                        "stix_id": obj.get("id"),
                        "description": obj.get("description", ""),
                        "aliases": obj.get("aliases", [])
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

        return observations

registry.register(StixAdapter)
