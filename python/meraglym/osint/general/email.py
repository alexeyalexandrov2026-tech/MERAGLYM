import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class EmailAdapter(BaseAdapter):
    """
    Adapter for investigating email addresses globally.
    Abstracts away the subprocess logic seen in tools like holehe,
    preparing a safe, bounded integration point.
    """
    identifier = "email_recon"
    region = "GLOBAL"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Executes an email recon job.
        """
        import re
        target_email = payload.get("value")
        
        # Harden integration boundary with strict validation
        if not target_email or not isinstance(target_email, str):
            raise ValueError("Email adapter requires a valid string 'value' in the payload.")
            
        email_regex = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        if not email_regex.match(target_email):
            raise ValueError(f"Invalid email format provided to adapter: {target_email}")

        import shutil
        has_ghunt = shutil.which("ghunt")
        has_holehe = shutil.which("holehe")
        
        if not has_ghunt and not has_holehe:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: ghunt or holehe executable not found in PATH.")
            
        observations = []
        
        return observations

# Register the adapter automatically
registry.register(EmailAdapter)
