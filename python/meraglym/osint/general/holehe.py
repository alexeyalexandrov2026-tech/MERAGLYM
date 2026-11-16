import re
from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import dependency_error, find_executable, run_tool, service_error

EMAIL_RE = re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")


class HoleheAdapter(BaseAdapter):
    """holehe: which of ~120 sites have an account registered to an email (no password-recovery probes)."""
    identifier = "holehe_recon"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        email = str(payload.get("value") or "").strip()
        if not EMAIL_RE.match(email):
            raise ValueError("INVALID_INPUT: holehe requires a valid email in 'value'.")
        exe = find_executable("holehe", "HOLEHE_PATH")
        if not exe:
            raise dependency_error("holehe executable not found (pip install holehe or set HOLEHE_PATH).")
        rc, out, err = await run_tool(
            [exe, email, "--no-color", "--no-clear", "-NP", "-T", "15"], timeout=240
        )
        if "websites checked" not in out:
            raise service_error(f"holehe did not complete (rc={rc}): {(err or out)[-300:]}")
        used, rate_limited, not_used = [], [], 0
        for line in out.splitlines():
            line = line.strip()
            if "Email used" in line:  # legend line
                continue
            if line.startswith("[+]"):
                used.append(line[3:].strip())
            elif line.startswith("[x]"):
                rate_limited.append(line[3:].strip())
            elif line.startswith("[-]"):
                not_used += 1
        m = re.search(r"(\d+) websites checked", out)
        summary = {
            "entity_type": "Email",
            "entity_value": email,
            "metadata": {
                "source": "holehe",
                "sites_checked": int(m.group(1)) if m else None,
                "used_on": used,
                "not_used_count": not_used,
                "rate_limited": rate_limited,
            },
            "confidence": 0.85,
            "reliability": 0.8,
        }
        accounts = [{
            "entity_type": "Account",
            "entity_value": f"{site}:{email}",
            "metadata": {"source": "holehe", "site": site, "email": email},
            "confidence": 0.85,
            "reliability": 0.8,
        } for site in used]
        return [summary, *accounts]


registry.register(HoleheAdapter)
