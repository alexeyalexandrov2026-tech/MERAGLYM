import glob
import json
import os
import re
import tempfile
from typing import Any, Dict, List
from urllib.parse import urlparse

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import dependency_error, find_executable, run_tool, service_error

USERNAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]{1,63}$")  # no leading "-" (argv option injection)


class SocialMediaAdapter(BaseAdapter):
    """Username search across social networks: Maigret (primary) + Social Analyzer (secondary).

    payload: {"value": "<username>", "top_sites": 500, "engines": ["maigret", "social-analyzer"]}
    """
    identifier = "social_recon"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        username = str(payload.get("value") or "").strip().lstrip("@")
        if not USERNAME_RE.match(username):
            raise ValueError("INVALID_INPUT: social_recon requires a username (letters, digits, _ . -).")
        top = max(10, min(int(payload.get("top_sites", 500)), 3000))
        engines = payload.get("engines") or ["maigret", "social-analyzer"]
        maigret = find_executable("maigret", "MAIGRET_PATH")
        sa = find_executable("social-analyzer", "SOCIAL_ANALYZER_PATH")
        if not maigret and not sa:
            raise dependency_error("neither maigret nor social-analyzer is installed.")
        obs: List[Dict[str, Any]] = []
        errors = []
        attempted = 0
        if maigret and "maigret" in engines:
            attempted += 1
            with tempfile.TemporaryDirectory(prefix="maigret-") as d:
                rc, out, err = await run_tool(
                    [maigret, username, "--top-sites", str(top), "--timeout", "10", "-J", "simple",
                     "-fo", d, "--no-progressbar", "--no-color", "--no-recursion"],
                    timeout=600, cwd=d,
                )
                files = glob.glob(os.path.join(d, "*.json"))
                if files:
                    with open(files[0], encoding="utf-8") as f:
                        data = json.load(f)
                    for site, info in data.items():
                        status = (info.get("status") or {}) if isinstance(info, dict) else {}
                        if status.get("status") != "Claimed":
                            continue
                        obs.append({
                            "entity_type": "Account",
                            # one entity per platform (entities dedupe on type+value)
                            "entity_value": f"{site}:{username}",
                            "metadata": {
                                "source": "maigret", "platform": site, "url": info.get("url_user"),
                                "tags": status.get("tags"), "ids": status.get("ids") or {},
                            },
                            "confidence": 0.85,
                            "reliability": 0.8,
                        })
                else:
                    errors.append(f"maigret rc={rc}: {(err or out)[-200:]}")
        if sa and "social-analyzer" in engines:
            attempted += 1
            rc, out, err = await run_tool(
                [sa, "--username", username, "--top", str(min(top, 300)), "--output", "json",
                 "--method", "find", "--mode", "fast", "--filter", "good"],
                timeout=600,
            )
            start = out.find("{")
            try:
                data = json.loads(out[start:]) if start >= 0 else {}
                seen = {o["metadata"].get("url") for o in obs}
                for site in data.get("detected", []):
                    link = site.get("link")
                    if link in seen:
                        continue
                    obs.append({
                        "entity_type": "Account",
                        "entity_value": f"{urlparse(link).hostname or link}:{username}",
                        "metadata": {"source": "social-analyzer", "url": link, "title": site.get("title"),
                                     "country": site.get("country"), "rate": site.get("rate"),
                                     "note": "social-analyzer detections are heuristic; verify manually"},
                        "confidence": 0.5,
                        "reliability": 0.7,
                    })
            except ValueError:
                errors.append(f"social-analyzer rc={rc}: {(err or out)[-200:]}")
        if not attempted:
            raise dependency_error(f"none of the requested engines {engines} is installed.")
        if errors and not obs and len(errors) == attempted:
            raise service_error("; ".join(errors))
        return obs


registry.register(SocialMediaAdapter)
