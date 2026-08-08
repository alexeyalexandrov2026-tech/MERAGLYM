import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class KadAdapter(BaseAdapter):
    """
    Russian Arbitration Court (KAD) Adapter.
    Leverages atomno-mcp-fns-check's KadClient to find active lawsuits.
    """
    identifier = "kad_arbitr"
    region = "RU"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = payload.get("value")
        if not inn or not isinstance(inn, str):
            raise ValueError("KadAdapter requires a valid 'value' (INN).")

        observations = []
        try:
            from atomno_mcp_fns_check.sources.kad import KadClient
        except ImportError:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: atomno-mcp-fns-check not installed.")

        try:
            async with KadClient() as client:
                cases = await client.search_active_lawsuits_by_inn(inn)
                
                for case in cases:
                    observations.append({
                        "entity_type": "LegalCase",
                        "entity_value": case.case_number,
                        "metadata": {
                            "source": "kad.arbitr.ru",
                            "role": case.role,
                            "amount_rub": case.amount_rub,
                            "status": case.status
                        },
                        "confidence": 0.95,
                        "reliability": 0.90
                    })
        except Exception as e:
            # Wrap as REQUIRES_EXTERNAL_SERVICE for graceful orchestration
            raise RuntimeError(f"REQUIRES_EXTERNAL_SERVICE: KAD fetch failed (Geo-blocked/RateLimited): {e}")

        return observations

registry.register(KadAdapter)
