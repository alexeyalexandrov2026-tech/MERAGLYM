import json
import os
import re
from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import dependency_error, run_tool, script_python, service_error

SAFE_TARGET = re.compile(r"^[A-Za-z0-9@._:\-/ \"]{1,253}$")
DEFAULT_MODULES = "sfp_dnsresolve,sfp_whois,sfp_sslcert"


class SpiderFootAdapter(BaseAdapter):
    """SpiderFoot 4 CLI scan (sf.py) of a domain / IP / email / username.

    payload: {"value": "example.com", "modules": "sfp_dnsresolve,sfp_whois"}  (or "use_case": "passive")
    """
    identifier = "spiderfoot_meta"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        target = str(payload.get("value") or "").strip()
        if not target or not SAFE_TARGET.match(target):
            raise ValueError("INVALID_INPUT: spiderfoot_meta requires a domain/IP/email/username in 'value'.")
        script = os.environ.get("SPIDERFOOT_PATH")
        if not script or not os.path.exists(script):
            raise dependency_error("SpiderFoot not found (set SPIDERFOOT_PATH to sf.py).")
        modules = str(payload.get("modules") or DEFAULT_MODULES)
        if not re.match(r"^[a-z0-9_,]+$", modules):
            raise ValueError("INVALID_INPUT: 'modules' must be a comma-separated list of sfp_* names.")
        cmd = [script_python(script, "SPIDERFOOT_PYTHON"), script, "-s", target, "-o", "json", "-q", "-max-threads", "3"]
        use_case = payload.get("use_case")
        if use_case in ("passive", "footprint", "investigate", "all"):
            cmd += ["-u", use_case]
        else:
            cmd += ["-m", modules]
        rc, out, err = await run_tool(cmd, timeout=int(payload.get("timeout", 600)), cwd=os.path.dirname(script))
        start = out.find("[")
        try:
            events = json.loads(out[start:]) if start >= 0 else None
        except ValueError:
            events = None
        if events is None:
            raise service_error(f"SpiderFoot returned no JSON (rc={rc}): {(err or out)[-300:]}")
        obs = []
        for ev in events:
            if ev.get("module") == "SpiderFoot UI":
                continue
            obs.append({
                "entity_type": str(ev.get("type") or "Entity"),
                "entity_value": str(ev.get("data"))[:1000],
                "metadata": {"source": f"spiderfoot:{ev.get('module')}", "target": target, "from": ev.get("source")},
                "confidence": 0.8,
                "reliability": 0.8,
            })
        return obs


registry.register(SpiderFootAdapter)
