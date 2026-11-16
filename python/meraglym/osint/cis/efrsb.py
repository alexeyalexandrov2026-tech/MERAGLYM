from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import require_inn
from meraglym.osint.cis._atomno import call, import_client, to_dict


class EfrsbAdapter(BaseAdapter):
    """EFRSB / Fedresurs (bankrot.fedresurs.ru) active bankruptcy cases by INN."""
    identifier = "efrsb_bankruptcy"
    region = "RU"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = require_inn(payload)
        import_client("efrsb", "EfrsbClient")
        cases = await call("bankrot.fedresurs.ru", "efrsb", "EfrsbClient", "search_active_by_inn", inn)
        return [{
            "entity_type": "BankruptcyCase",
            "entity_value": c.case_number or inn,
            "metadata": {"source": "bankrot.fedresurs.ru", "inn": inn, **to_dict(c)},
            "confidence": 0.95,
            "reliability": 0.9,
        } for c in cases or []]


registry.register(EfrsbAdapter)
