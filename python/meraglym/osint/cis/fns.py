from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import require_inn
from meraglym.osint.cis._atomno import call, import_client, to_dict


class FnsAdapter(BaseAdapter):
    """FNS "Прозрачный бизнес" (pb.nalog.ru) company card: status, region, OKVED, flags."""
    identifier = "fns_tax"
    region = "RU"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = require_inn(payload)
        import_client("pb_fns", "PbFnsClient")
        card = await call("pb.nalog.ru", "pb_fns", "PbFnsClient", "get_company_card", inn)
        if not card:
            return []
        return [{
            "entity_type": "Company",
            "entity_value": inn,
            "metadata": {"source": "pb.nalog.ru", **to_dict(card)},
            "confidence": 0.97,
            "reliability": 0.95,
        }]


registry.register(FnsAdapter)
