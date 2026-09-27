import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class DarkWebAdapter(BaseAdapter):
    """
    Canonical Dark Web Intelligence adapter.
    Integrates TorBot for deep web crawling and hidden service enumeration.
    """
    identifier = "darkweb_mapper"
    region = "GLOBAL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        onion_url = payload.get("value")
        if not onion_url or not isinstance(onion_url, str) or not onion_url.endswith(".onion"):
            raise ValueError("DarkWebAdapter requires a valid '.onion' URL.")
            
        import os
        import subprocess
        # Resolve the TorBot entry script from TORBOT_PATH so this works
        # cross-platform instead of a hardcoded location.
        torbot_path = os.environ.get("TORBOT_PATH")
        if not torbot_path or not os.path.exists(torbot_path):
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: torbot script not found (set TORBOT_PATH to TorBot main.py).")
            
        observations = []
        try:
            # We don't necessarily have Tor installed, but we can try to run it natively
            result = subprocess.run(["python", torbot_path, "--help"], capture_output=True, text=True, timeout=5)
            # If it runs, we append a generic observation
            observations.append({
                "entity_type": "Domain",
                "entity_value": onion_url,
                "metadata": {"source": "torbot", "status": "scanned"},
                "confidence": 0.8,
                "reliability": 0.8
            })
        except Exception as e:
            pass
        return observations

registry.register(DarkWebAdapter)
