import ipaddress
import json
import os
import tempfile
from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import dependency_error, run_tool, script_python, service_error


class CameraAdapter(BaseAdapter):
    """IP camera discovery/fingerprinting (HTTP/RTSP/ONVIF) on a single IP or small CIDR,
    using CCTV-scanner `latest.py` (CCTVSCAN_PATH).

    Safety: by default only private/loopback targets are allowed. Scanning public IPs
    you do not own may violate the hosting provider's acceptable-use policy; enable it
    explicitly with CAMERA_SCAN_ALLOW_PUBLIC=1.
    """
    identifier = "camera_recon"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        value = str(payload.get("value") or "").strip()
        try:
            net = ipaddress.ip_network(value, strict=False)
        except ValueError:
            raise ValueError("INVALID_INPUT: camera_recon requires an IP address or CIDR in 'value'.")
        if net.num_addresses > 256:
            raise ValueError("INVALID_INPUT: camera_recon accepts at most a /24.")
        allow_public = os.environ.get("CAMERA_SCAN_ALLOW_PUBLIC") == "1"
        if not allow_public and not (net.is_private or net.is_loopback):
            raise ValueError(
                "INVALID_INPUT: scanning public IPs is disabled on this worker (set CAMERA_SCAN_ALLOW_PUBLIC=1 "
                "only for targets you are authorised to test)."
            )
        script = os.environ.get("CCTVSCAN_PATH")
        if not script or not os.path.exists(script):
            raise dependency_error("CCTV scanner not found (set CCTVSCAN_PATH to CCTV-scanner latest.py).")
        with tempfile.TemporaryDirectory(prefix="cctv-") as d:
            out_file = os.path.join(d, "out.json")
            cmd = [script_python(script, "CCTVSCAN_PYTHON"), script, str(net if net.num_addresses > 1 else net.network_address),
                   "-o", out_file, "--max-memory", "1"]
            if payload.get("extended"):
                cmd.append("--extended")
            rc, out, err = await run_tool(cmd, timeout=600, cwd=d)
            if not os.path.exists(out_file):
                raise service_error(f"CCTV scanner produced no output (rc={rc}): {(err or out)[-300:]}")
            with open(out_file, encoding="utf-8") as f:
                data = json.load(f)
        info = data.get("scan_info", {})
        obs = [{
            "entity_type": "NetworkScan",
            "entity_value": str(net),
            "metadata": {"source": "cctv-scanner", **info},
            "confidence": 1.0,
            "reliability": 0.9,
        }]
        for cam in data.get("cameras", []):
            obs.append({
                "entity_type": "Device",
                "entity_value": str(cam.get("ip") or cam.get("host") or net),
                "metadata": {"source": "cctv-scanner", **{k: v for k, v in cam.items() if k != "snippet"}},
                "confidence": float(cam.get("confidence_score", 0.8)) if isinstance(cam.get("confidence_score"), (int, float)) else 0.8,
                "reliability": 0.8,
            })
        return obs


registry.register(CameraAdapter)
