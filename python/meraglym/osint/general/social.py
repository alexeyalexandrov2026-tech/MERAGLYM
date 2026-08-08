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
                env["PYTHONUTF8"] = "1"
                # Use maigret to check the username. 
                # --timeout 3 limits the wait. -J simple produces a JSON report in reports/ dir
                cmd = ["maigret", target_username, "--timeout", "3", "-J", "simple", "--no-extracting", "--no-color"]
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
                else:
                    print(f"Maigret report not found. Stdout: {result.stdout}, Stderr: {result.stderr}")
            except Exception as e:
                print(f"Maigret exception: {e}")
                
        # Social Analyzer execution if missing maigret or if we want to augment
        sa_script = r"C:\Users\alexa\OneDrive\Desktop\MERAGLYM_unpacked\social-analyzer-main\social-analyzer-main\app.py"
        has_sa_script = os.path.exists(sa_script)
        
        if has_sa_script and not observations:
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                # Set path so that modules load correctly
                env["PYTHONPATH"] = r"C:\Users\alexa\OneDrive\Desktop\MERAGLYM_unpacked\social-analyzer-main\social-analyzer-main"
                
                cmd = ["python", sa_script, "--username", target_username, "--output", "json", "--top", "50"]
                result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
                
                # social analyzer outputs JSON directly to stdout
                try:
                    # Sometimes it outputs some logs before JSON, find the first '{' or '['
                    out = result.stdout
                    json_start = out.find('{')
                    if json_start != -1:
                        data = json.loads(out[json_start:])
                        # Format is {"detected": [{"name": "site", "url": "url", ...}]}
                        detected = data.get("detected", [])
                        for site in detected:
                            observations.append({
                                "entity_type": "Person",
                                "entity_value": target_username,
                                "metadata": {
                                    "platform": site.get("name"),
                                    "url": site.get("url"),
                                    "source": "social-analyzer"
                                },
                                "confidence": 0.85,
                                "reliability": 0.80
                            })
                except Exception as ex:
                    pass
            except Exception as e:
                pass
                
        if not observations and not has_maigret and not has_sa_script:
             raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: Maigret and Social Analyzer failed or missing.")
        
        return observations

registry.register(SocialMediaAdapter)
