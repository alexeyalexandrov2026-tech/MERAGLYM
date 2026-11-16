import json
import os
import re
from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import dependency_error, run_tool, script_python, service_error

BSSID_RE = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$")


class GeospatialAdapter(BaseAdapter):
    """GeoWiFi: geolocate a Wi-Fi BSSID (or SSID) via Apple, Mylnikov, WifiDB, Freifunk
    (keyless) and WiGLE / Google / Combain (need keys in geowifi's gw_utils/config.yaml)."""
    identifier = "geospatial_mapper"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        value = str(payload.get("value") or "").strip()
        if not value:
            raise ValueError("INVALID_INPUT: geospatial_mapper requires a BSSID or SSID in 'value'.")
        search_by = "bssid" if BSSID_RE.match(value) else "ssid"
        if search_by == "bssid":
            value = value.replace("-", ":").upper()
        elif not re.match(r"^[\w .\-]{1,32}$", value):
            raise ValueError("INVALID_INPUT: SSID contains unsupported characters.")
        script = os.environ.get("GEOWIFI_PATH")
        if not script or not os.path.exists(script):
            raise dependency_error("GeoWiFi not found (set GEOWIFI_PATH to geowifi.py).")
        base = os.path.dirname(os.path.abspath(script))
        rc, out, err = await run_tool(
            [script_python(script, "GEOWIFI_PYTHON"), script, "-s", search_by, "-o", "json", value],
            timeout=180, cwd=base,
        )
        name = re.sub(r"[^A-Za-z0-9]", "_", value)
        path = os.path.join(base, "results", f"{name}.json")
        if not os.path.exists(path):
            raise service_error(f"GeoWiFi produced no result file (rc={rc}): {(err or out)[-300:]}")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        rows = data if isinstance(data, list) else data.get("results", [data]) if isinstance(data, dict) else []
        obs = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            lat, lon = r.get("latitude"), r.get("longitude")
            if lat in (None, "", "❌") or lon in (None, "", "❌"):
                continue
            obs.append({
                "entity_type": "Location",
                "entity_value": f"{lat},{lon}",
                "metadata": {"source": f"geowifi:{r.get('module')}", "query": value, "bssid": r.get("bssid"),
                             "ssid": r.get("ssid"), "latitude": lat, "longitude": lon},
                "confidence": 0.7,
                "reliability": 0.75,
            })
        return obs


registry.register(GeospatialAdapter)
