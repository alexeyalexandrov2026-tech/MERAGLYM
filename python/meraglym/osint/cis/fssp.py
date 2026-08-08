import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class FsspAdapter(BaseAdapter):
    """
    Russian Federal Bailiff Service (FSSP) Adapter.
    Finds enforcement proceedings via atomno-mcp-fns-check.
    """
    identifier = "fssp_check"
    region = "RU"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = payload.get("value")
        if not inn or not isinstance(inn, str):
            raise ValueError("FsspAdapter requires a valid 'value' (INN).")

        observations = []
        try:
            from atomno_mcp_fns_check.sources.fssp import FsspClient
        except ImportError:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: atomno-mcp-fns-check not installed.")

        try:
            async with FsspClient() as client:
                debts = await client.search_proceedings_by_inn(inn)
                
                for debt in debts:
                    observations.append({
                        "entity_type": "Debt",
                        "entity_value": debt.ip_number,
                        "metadata": {
                            "source": "fssp.gov.ru",
                            "amount_rub": debt.amount_rub,
                            "subject": debt.subject,
                            "department": debt.department
                        },
                        "confidence": 0.95,
                        "reliability": 0.90
                    })
        except Exception as e:
            raise RuntimeError(f"REQUIRES_EXTERNAL_SERVICE: FSSP fetch failed (API Offline): {e}")

        return observations

registry.register(FsspAdapter)
