from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import require_str, ru_http_client, ru_service_error


class SudrfAdapter(BaseAdapter):
    """ГАС «Правосудие» (bsr.sudrf.ru) full-text court decision search by name/INN.

    The portal is only reachable from Russian IPs; set RU_PROXY_URL on non-RU hosts.
    """
    identifier = "sudrf_courts"
    region = "RU"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        target = require_str(payload, what="name or INN")
        import json
        # Simple full-text query in the format used by the portal's own search box.
        # NOTE: only verifiable from a Russian IP; response parsing is defensive.
        request = {
            "start": 0, "rows": int(payload.get("rows", 20)), "uid": "", "type": "MULTIQUERY",
            "multiqueryRequest": {"queryRequests": []}, "sorts": [],
            "simpleSearchFieldsBundle": "default", "noOrder": False,
            "groups": ["Решения по делам"], "text": target,
        }
        try:
            async with ru_http_client(timeout=40.0) as client:
                r = await client.post(
                    "https://bsr.sudrf.ru/bigs/s.action",
                    data={"request": json.dumps(request)},
                    headers={"Referer": "https://bsr.sudrf.ru/bigs/portal.html", "Accept": "application/json"},
                )
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            raise ru_service_error("bsr.sudrf.ru", e)
        docs = (data.get("searchResult") or {}).get("documents") or []
        obs = []
        for d in docs:
            fields = {f.get("name"): f.get("value") for f in d.get("additionalFields", []) if isinstance(f, dict)}
            obs.append({
                "entity_type": "LegalCase",
                "entity_value": fields.get("case_number") or d.get("id") or target,
                "metadata": {"source": "bsr.sudrf.ru", "query": target, "doc_id": d.get("id"), "fields": fields},
                "confidence": 0.85,
                "reliability": 0.85,
            })
        return obs


registry.register(SudrfAdapter)
