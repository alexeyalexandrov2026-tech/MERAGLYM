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
        
        if not has_ghunt:
            raise RuntimeError("REQUIRES_USER_CREDENTIAL: ghunt executable not found or not authenticated.")
            
        observations = []
        
        if has_ghunt:
            try:
                import os, subprocess, json
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                
                # Use GHunt with JSON output
                # ghunt email target@email.com --json out.json
                cmd = ["ghunt", "email", target_email, "--json", f"ghunt_{target_email}.json"]
                result = subprocess.run(cmd, capture_output=True, text=True, env=env, encoding="utf-8")
                
                if "Login failed" in result.stderr or "auth" in result.stderr.lower():
                    raise RuntimeError("REQUIRES_USER_CREDENTIAL: GHunt requires valid session. Run 'ghunt login'.")
                    
                json_file = f"ghunt_{target_email}.json"
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Assuming we get some data
                    if data:
                        observations.append({
                            "entity_type": "Email",
                            "entity_value": target_email,
                            "metadata": {
                                "source": "ghunt",
                                "raw_data": data
                            },
                            "confidence": 1.0,
                            "reliability": 0.95
                        })
                    try:
                        os.remove(json_file)
                    except:
                        pass
            except RuntimeError as re:
                # Re-raise the credential missing error so it gets caught properly by the worker
                raise re
            except Exception as e:
                pass
                
        return observations

# Register the adapter automatically
registry.register(EmailAdapter)
