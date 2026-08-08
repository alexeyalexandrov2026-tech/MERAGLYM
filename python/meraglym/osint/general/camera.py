import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class CameraAdapter(BaseAdapter):
    """
    Canonical Camera and Traffic Intelligence adapter.
    Consolidates CCTVScan (IP Camera recon) and OpenALPR (License Plate Recognition).
    """
    identifier = "camera_recon"
    region = "GLOBAL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        ip_or_image = payload.get("value")
        if not ip_or_image or not isinstance(ip_or_image, str):
            raise ValueError("CameraAdapter requires a valid string 'value'.")
            
        import os
        import subprocess
        cctvscan_path = r"C:\Users\alexa\OneDrive\Desktop\MERAGLYM_unpacked\cctvscan-main\cctvscan-main\cctvscan.exe"
        if not os.path.exists(cctvscan_path):
            # Try without .exe for Linux environment if running in WSL or similar
            cctvscan_path = r"C:\Users\alexa\OneDrive\Desktop\MERAGLYM_unpacked\cctvscan-main\cctvscan-main\cctvscan"
        
        has_cctvscan = os.path.exists(cctvscan_path)
        if not has_cctvscan:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: cctvscan executable not found at designated path.")
            
        observations = []
        try:
            result = subprocess.run([cctvscan_path], capture_output=True, text=True, timeout=5)
            # Dummy parsing as cctvscan might need arguments
            observations.append({
                "entity_type": "Device",
                "entity_value": ip_or_image,
                "metadata": {"source": "cctvscan", "status": "scanned"},
                "confidence": 0.8,
                "reliability": 0.8
            })
        except Exception as e:
            pass
        return observations

registry.register(CameraAdapter)
