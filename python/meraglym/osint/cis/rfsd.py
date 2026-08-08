import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class RfsdAdapter(BaseAdapter):
    """
    Adapter for processing the Russian Financial Statements Database (RFSD).
    Incrementally maps unconsolidated financial statements to MERAGLYM Entities.
    """
    identifier = "rfsd_financials"
    region = "CIS"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        target_inn = payload.get("inn")
        if not target_inn:
            raise ValueError("RFSD adapter requires a target 'inn' (Tax ID).")

        import httpx
        observations = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://bo.nalog.ru/nbo/organizations/search?query={target_inn}",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("content", [])
                    for item in content:
                        observations.append({
                            "entity_type": "FinancialStatement",
                            "entity_value": target_inn,
                            "metadata": {
                                "source": "bo.nalog.ru",
                                "name": item.get("shortName"),
                                "bfo_status": item.get("bfoStatus")
                            },
                            "confidence": 0.99,
                            "reliability": 0.99
                        })
        except Exception as e:
            raise RuntimeError(f"RFSD fetch failed: {e}")

        return observations

registry.register(RfsdAdapter)
