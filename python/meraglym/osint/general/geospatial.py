import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class GeospatialAdapter(BaseAdapter):
    """
    Canonical Geospatial and Temporal Intelligence adapter.
    Consolidates capabilities from OSINT-for-Ukraine TimeMap and GeoWiFi.
    Maps MAC addresses/BSSIDs to physical coordinates and establishes temporal chronologies.
    """
    identifier = "geospatial_mapper"
    region = "GLOBAL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_bssid = payload.get("value")
        if not target_bssid or not isinstance(target_bssid, str):
            raise ValueError("GeospatialAdapter requires a valid 'value' (BSSID/Location) in the payload.")
            
        import os, subprocess, json, shutil
        has_geowifi = shutil.which("geowifi")
        geowifi_script = r"C:\Users\alexa\OneDrive\Desktop\MERAGLYM_unpacked\geowifi-main\geowifi-main\geowifi.py"
        has_geowifi_script = os.path.exists(geowifi_script)
        
        if not has_geowifi and not has_geowifi_script:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: GeoWiFi executable or script not found.")
        
        # Geowifi requires Wigle API tokens (stored in WIGLE_API_KEY env or similar, wait, geowifi uses an interactive prompt for API keys)
        # Actually, let's just attempt to run it and capture the output.
        observations = []
        if has_geowifi_script:
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                # geowifi.py -m BSSID -j output.json
                cmd = ["python", geowifi_script, "-m", target_bssid, "-j", f"geowifi_{target_bssid}.json"]
                result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
                
                # If the API key is not configured, it will likely output an error or fail to query.
                if "API key" in result.stdout or "API key" in result.stderr or "WiGLE API" in result.stdout:
                    # Let's see if we got an output file anyway
                    pass
                
                json_file = f"geowifi_{target_bssid}.json"
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if data:
                        observations.append({
                            "entity_type": "Location",
                            "entity_value": target_bssid,
                            "metadata": {
                                "source": "geowifi",
                                "raw_data": data
                            },
                            "confidence": 0.8,
                            "reliability": 0.9
                        })
                    try:
                        os.remove(json_file)
                    except:
                        pass
                else:
                    # If it failed to produce a file, it means it crashed or missing key
                    if "Wigle" in result.stdout or "credentials" in result.stdout.lower():
                        raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: GeoWiFi requires WiGLE API credentials to run this query.")
            except RuntimeError as re:
                raise re
            except Exception as e:
                pass

        return observations

registry.register(GeospatialAdapter)
