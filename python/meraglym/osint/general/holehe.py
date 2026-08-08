import asyncio
import os
import subprocess
import shutil
import json
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class HoleheAdapter(BaseAdapter):
    """
    Adapter for investigating email addresses globally using holehe.
    """
    identifier = "holehe_recon"
    region = "GLOBAL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_email = payload.get("value")
        if not target_email or not isinstance(target_email, str):
            raise ValueError("Holehe adapter requires a valid string 'value' in the payload.")
            
        has_holehe = shutil.which("holehe")
        if not has_holehe:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: holehe executable not found in PATH.")
            
        observations = []
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            cmd = ["holehe", target_email, "--only-used", "--no-color"]
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
            
            for line in result.stdout.splitlines():
                if "[+]" in line:
                    site = line.replace("[+]", "").strip()
                    observations.append({
                        "entity_type": "Account",
                        "entity_value": target_email,
                        "metadata": {
                            "source": "holehe",
                            "site": site
                        },
                        "confidence": 0.90,
                        "reliability": 0.85
                    })
        except Exception as e:
            pass
            
        return observations

registry.register(HoleheAdapter)
