import json
import os
import re
import tempfile
from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import credential_error, dependency_error, find_executable, run_tool, service_error

EMAIL_RE = re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")


def ghunt_creds_path() -> str:
    return os.path.expanduser(os.environ.get("GHUNT_CREDS_PATH", "~/.malfrats/ghunt/creds.m"))


class EmailAdapter(BaseAdapter):
    """GHunt: Google account intelligence for an email (Gaia ID, profile, Maps reviews, etc.).

    Needs a GHunt session on the worker host: run `ghunt login` as the worker user once.
    """
    identifier = "email_recon"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        email = str(payload.get("value") or "").strip()
        if not EMAIL_RE.match(email):
            raise ValueError("INVALID_INPUT: email_recon requires a valid email in 'value'.")
        exe = find_executable("ghunt", "GHUNT_PATH")
        if not exe:
            raise dependency_error("ghunt executable not found (pip install ghunt or set GHUNT_PATH).")
        if not os.path.exists(ghunt_creds_path()):
            raise credential_error(
                "GHunt has no Google session. As the worker user run `ghunt login` "
                "(GHunt Companion browser extension, a throwaway Google account is recommended)."
            )
        with tempfile.TemporaryDirectory(prefix="ghunt-") as d:
            out_file = os.path.join(d, "out.json")
            rc, out, err = await run_tool([exe, "email", email, "--json", out_file], timeout=180, cwd=d)
            text = out + err
            if "GHuntInvalidSession" in text or "ghunt login" in text:
                raise credential_error("GHunt session is invalid/expired; run `ghunt login` again as the worker user.")
            if not os.path.exists(out_file):
                if "not found" in text.lower() or "doesn't exist" in text.lower():
                    return []
                raise service_error(f"GHunt failed (rc={rc}): {text[-300:]}")
            with open(out_file, encoding="utf-8") as f:
                data = json.load(f)
        return [{
            "entity_type": "Email",
            "entity_value": email,
            "metadata": {"source": "ghunt", "raw_data": data},
            "confidence": 0.95,
            "reliability": 0.9,
        }] if data else []


registry.register(EmailAdapter)
