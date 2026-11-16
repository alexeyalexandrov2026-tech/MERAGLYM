from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import require_inn
from meraglym.osint.cis._atomno import call, import_client, to_dict


class KadAdapter(BaseAdapter):
    """Arbitration courts card index (kad.arbitr.ru): active lawsuits by INN."""
    identifier = "kad_arbitr"
    region = "RU"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = require_inn(payload)
        import_client("kad", "KadClient")
        cases = await call("kad.arbitr.ru", "kad", "KadClient", "search_active_lawsuits_by_inn", inn)
        return [{
            "entity_type": "LegalCase",
            "entity_value": c.case_number or inn,
            "metadata": {"source": "kad.arbitr.ru", "inn": inn, **to_dict(c)},
            "confidence": 0.95,
            "reliability": 0.9,
        } for c in cases or []]


registry.register(KadAdapter)
