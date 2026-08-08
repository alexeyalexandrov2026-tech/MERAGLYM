import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class EfrsbAdapter(BaseAdapter):
    """
    Russian Unified Federal Register of Bankruptcy (EFRSB) Adapter.
    Finds bankruptcy statuses via atomno-mcp-fns-check.
    """
    identifier = "efrsb_bankruptcy"
    region = "RU"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = payload.get("value")
        if not inn or not isinstance(inn, str):
            raise ValueError("EfrsbAdapter requires a valid 'value' (INN).")

        observations = []
        try:
            from atomno_mcp_fns_check.sources.efrsb import EfrsbClient
        except ImportError:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: atomno-mcp-fns-check not installed.")

        try:
            async with EfrsbClient() as client:
                cases = await client.search_active_by_inn(inn)
                
                for case in cases:
                    observations.append({
                        "entity_type": "Bankruptcy",
                        "entity_value": inn,
                        "metadata": {
                            "source": "bankrot.fedresurs.ru",
                            "status": case.status,
                            "is_active": case.is_active,
                            "debtor_name": case.debtor_name
                        },
                        "confidence": 0.95,
                        "reliability": 0.90
                    })
        except Exception as e:
            raise RuntimeError(f"REQUIRES_EXTERNAL_SERVICE: EFRSB fetch failed (API Error): {e}")

        return observations

registry.register(EfrsbAdapter)
