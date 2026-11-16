from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import require_inn
from meraglym.osint.cis._atomno import call, import_client, to_dict


class FsspAdapter(BaseAdapter):
    """FSSP data bank (is-go.fssp.gov.ru) enforcement proceedings by company INN."""
    identifier = "fssp_check"
    region = "RU"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = require_inn(payload)
        import_client("fssp", "FsspClient")
        items = await call("is-go.fssp.gov.ru", "fssp", "FsspClient", "search_proceedings_by_inn", inn)
        return [{
            "entity_type": "EnforcementProceeding",
            "entity_value": p.case_number or inn,
            "metadata": {"source": "fssp.gov.ru", "inn": inn, "is_open": p.is_open, **to_dict(p)},
            "confidence": 0.95,
            "reliability": 0.9,
        } for p in items or []]


registry.register(FsspAdapter)
