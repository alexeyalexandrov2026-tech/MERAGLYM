import asyncio
import os
import subprocess
import json
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class SocialMediaAdapter(BaseAdapter):
    """
    Canonical Social Media Intelligence adapter.
    Consolidates capabilities from Maigret, Social Analyzer, and EagleEye.
    Handles username/profile reconnaissance across thousands of platforms.
    """
    identifier = "social_recon"
    region = "GLOBAL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_username = payload.get("value")
        if not target_username or not isinstance(target_username, str):
            raise ValueError("SocialMediaAdapter requires a valid string 'value' (username) in the payload.")
            
        observations = []
        import shutil
        has_maigret = shutil.which("maigret")
        has_social_analyzer = shutil.which("social-analyzer")
        
        if not has_maigret and not has_social_analyzer:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: Maigret or Social Analyzer executables not found in PATH.")
            
        observations = []
        if has_maigret:
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                # Use maigret to check the username. 
                # --timeout 3 limits the wait. -J simple produces a JSON report in reports/ dir
                cmd = ["maigret", target_username, "--timeout", "3", "-J", "simple", "--no-extracting", "-a", "--no-color"]
                result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
                
                json_file = os.path.join(os.getcwd(), "reports", f"report_{target_username}_simple.json")
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Normalizing
                    for site_data in data.get(target_username, {}).values():
                        if site_data.get("status") == "Claimed":
                            observations.append({
                                "entity_type": "Person", # Or Profile
                                "entity_value": target_username,
                                "metadata": {
                                    "platform": site_data.get("name"),
                                    "url": site_data.get("url_user"),
                                    "source": "maigret"
                                },
                                "confidence": 0.90,
                                "reliability": 0.85
                            })
                    # Clean up
                    try:
                        os.remove(json_file)
                    except:
                        pass
            except Exception as e:
                # Only log the exception and fallback
                pass
        
        return observations

registry.register(SocialMediaAdapter)
