from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import require_inn, ru_http_client, ru_service_error


class RfsdAdapter(BaseAdapter):
    """Russian financial statements (ГИР БО, bo.nalog.ru): organisation search by INN."""
    identifier = "rfsd_financials"
    region = "RU"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = require_inn(payload)
        try:
            async with ru_http_client(timeout=30.0) as client:
                r = await client.get(
                    "https://bo.nalog.ru/advanced-search/organizations/search",
                    params={"query": inn, "page": 0},
                    headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0", "Referer": "https://bo.nalog.ru/"},
                )
                if r.status_code == 404:
                    r = await client.get(
                        "https://bo.nalog.ru/nbo/organizations/search",
                        params={"query": inn, "page": 0},
                        headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
                    )
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            raise ru_service_error("bo.nalog.ru", e)
        items = data.get("content", []) if isinstance(data, dict) else []
        return [{
            "entity_type": "FinancialStatement",
            "entity_value": str(it.get("inn") or inn),
            "metadata": {
                "source": "bo.nalog.ru",
                "org_id": it.get("id"),
                "name": it.get("shortName") or it.get("fullName"),
                "ogrn": it.get("ogrn"),
                "bfo": it.get("bfo") or it.get("bfoStatus"),
                "url": f"https://bo.nalog.ru/organizations-card/{it.get('id')}" if it.get("id") else None,
            },
            "confidence": 0.99,
            "reliability": 0.99,
        } for it in items]


registry.register(RfsdAdapter)
