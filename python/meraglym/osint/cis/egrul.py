from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import require_inn
from meraglym.osint.cis._atomno import call, import_client, to_dict


class EgrulAdapter(BaseAdapter):
    """EGRUL/EGRIP (egrul.nalog.ru) company/entrepreneur lookup by INN or OGRN."""
    identifier = "egrul_registry"
    region = "RU"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        value = payload.get("value")
        if not value and payload.get("pdf_url"):
            raise ValueError("INVALID_INPUT: EGRUL PDF parsing is not supported; pass 'value' (INN/OGRN).")
        import_client("egrul", "EgrulClient")  # fail fast if the library is missing
        value = str(value or "").strip()
        if value.isdigit() and len(value) in (13, 15):
            hits = await call("egrul.nalog.ru", "egrul", "EgrulClient", "search_by_ogrn", value)
        else:
            value = require_inn({"value": value})
            hits = await call("egrul.nalog.ru", "egrul", "EgrulClient", "search_by_inn", value)
        return [
            {
                "entity_type": "Company",
                "entity_value": h.inn or value,
                "metadata": {"source": "egrul.nalog.ru", **to_dict(h)},
                "confidence": 0.99,
                "reliability": 0.95,
            }
            for h in hits or []
        ]


registry.register(EgrulAdapter)
