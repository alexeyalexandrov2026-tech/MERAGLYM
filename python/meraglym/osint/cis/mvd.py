from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import require_str, ru_http_client, ru_service_error


class MvdAdapter(BaseAdapter):
    """MVD federal wanted list (мвд.рф/wanted) search by surname / full name.

    мвд.рф rejects most non-RU IPs; set RU_PROXY_URL on non-RU hosts.
    """
    identifier = "mvd_wanted"
    region = "RU"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        target = require_str(payload, what="surname or full name")
        parts = target.split()
        params = {"last_name": parts[0]}
        if len(parts) > 1:
            params["first_name"] = parts[1]
        if len(parts) > 2:
            params["middle_name"] = parts[2]
        try:
            async with ru_http_client(timeout=30.0) as client:
                r = await client.get("https://xn--b1aew.xn--p1ai/wanted", params=params)
                r.raise_for_status()
                html = r.text
        except Exception as e:
            raise ru_service_error("мвд.рф", e)
        import re
        obs = []
        # Cards look like <div class="bs-item ..."> ... <a href="/wanted/person/123">ФИО</a> ... birth date
        for m in re.finditer(r'href="(/wanted/[^"]+)"[^>]*>\s*([^<]{3,120})</a>', html):
            name = re.sub(r"\s+", " ", m.group(2)).strip()
            if parts[0].lower() not in name.lower():
                continue
            obs.append({
                "entity_type": "Person",
                "entity_value": name,
                "metadata": {"source": "мвд.рф/wanted", "query": target, "url": "https://xn--b1aew.xn--p1ai" + m.group(1)},
                "confidence": 0.7,
                "reliability": 0.9,
            })
        return obs


registry.register(MvdAdapter)
