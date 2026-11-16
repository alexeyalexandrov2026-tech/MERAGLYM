import json
import os
import re
import tempfile
from typing import Any, Dict, List
from urllib.parse import urlparse

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import dependency_error, run_tool, script_python, service_error

ONION_RE = re.compile(r"^[a-z2-7]{56}\.onion$")


class DarkWebAdapter(BaseAdapter):
    """Crawl a Tor hidden service with TorBot through the local Tor SOCKS proxy.

    payload: {"value": "http://<v3>.onion", "depth": 1}
    Needs: TORBOT_PATH (TorBot main.py) and a running tor daemon (TOR_SOCKS_HOST/PORT, default 127.0.0.1:9050).
    """
    identifier = "darkweb_mapper"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = str(payload.get("value") or "").strip()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        host = (urlparse(url).hostname or "").lower()
        if not ONION_RE.match(host):
            raise ValueError("INVALID_INPUT: darkweb_mapper requires a v3 '.onion' URL.")
        script = os.environ.get("TORBOT_PATH")
        if not script or not os.path.exists(script):
            raise dependency_error("TorBot not found (set TORBOT_PATH to TorBot main.py).")
        socks_host = os.environ.get("TOR_SOCKS_HOST", "127.0.0.1")
        socks_port = os.environ.get("TOR_SOCKS_PORT", "9050")
        import socket
        try:
            socket.create_connection((socks_host, int(socks_port)), timeout=3).close()
        except OSError:
            raise dependency_error(f"Tor SOCKS proxy not reachable at {socks_host}:{socks_port} (install/start tor).")
        depth = max(1, min(int(payload.get("depth", 1)), 2))
        with tempfile.TemporaryDirectory(prefix="torbot-") as d:
            rc, out, err = await run_tool(
                [script_python(script, "TORBOT_PYTHON"), script, "-u", url, "--depth", str(depth), "-q",
                 "--host", socks_host, "--port", str(socks_port), "--save", "json"],
                timeout=int(payload.get("timeout", 420)), cwd=d,
                env={"TORBOT_DATA_DIR": d, "HOME": os.environ.get("HOME", d)},
            )
            files = [os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.endswith(".json")]
            data = None
            if files:
                with open(sorted(files, key=os.path.getmtime)[-1], encoding="utf-8") as f:
                    data = json.load(f)
        links = set()

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k in ("url", "link", "href") and isinstance(v, str):
                        links.add(v)
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, str) and node.startswith("http"):
                links.add(node)

        walk(data)
        if not data:
            for m in re.finditer(r"https?://[^\s\"'<>]+", out):
                links.add(m.group(0).rstrip(").,"))
        if not links:
            raise service_error(f"TorBot returned no data for {host} (rc={rc}): {(err or out)[-300:]}")
        obs = [{
            "entity_type": "Domain",
            "entity_value": host,
            "metadata": {"source": "torbot", "url": url, "links_found": len(links)},
            "confidence": 0.9,
            "reliability": 0.8,
        }]
        for link in sorted(links)[:200]:
            if link.rstrip("/") == url.rstrip("/"):
                continue
            obs.append({
                "entity_type": "URL",
                "entity_value": link[:1000],
                "metadata": {"source": "torbot", "found_on": url, "onion": ".onion" in link},
                "confidence": 0.8,
                "reliability": 0.8,
            })
        return obs


registry.register(DarkWebAdapter)
