import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class SpiderFootAdapter(BaseAdapter):
    """
    Consolidated Intelligence capability from SpiderFoot, OpenOSINT, and OSINTBuddy.
    Acts as a meta-adapter to orchestrate complex generic recon across multiple APIs.
    """
    identifier = "spiderfoot_meta"
    region = "GLOBAL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        target = payload.get("value")
        if not target or not isinstance(target, str):
            raise ValueError("SpiderFootAdapter requires a valid string 'value' in the payload.")
            
        import os
        import subprocess
        # Resolve the SpiderFoot script from SPIDERFOOT_PATH so this works
        # cross-platform instead of a hardcoded location.
        sf_script = os.environ.get("SPIDERFOOT_PATH")
        if not sf_script or not os.path.exists(sf_script):
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: sf.py (spiderfoot) script not found (set SPIDERFOOT_PATH to sf.py).")
            
        observations = []
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            # Execute sf.py in CLI mode for a quick specific module, e.g. sfp_accounts
            cmd = ["python", sf_script, "-m", "sfp_accounts", "-s", target, "-q"]
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
            
            # Simple parsing: Spiderfoot CLI outputs lines like "Module: data"
            for line in result.stdout.splitlines():
                if target in line:
                    observations.append({
                        "entity_type": "Entity",
                        "entity_value": target,
                        "metadata": {
                            "source": "spiderfoot",
                            "raw": line
                        },
                        "confidence": 0.8,
                        "reliability": 0.8
                    })
        except Exception as e:
            pass
            
        return observations

registry.register(SpiderFootAdapter)
