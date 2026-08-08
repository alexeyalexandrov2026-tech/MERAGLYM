import asyncio
from typing import Any, Dict, List
from meraglym.osint import BaseAdapter, registry

class FnsAdapter(BaseAdapter):
    """
    Russian Federal Tax Service (FNS) Adapter.
    Combines EGRUL (extracts) and Transparent Business API via atomno-mcp-fns-check.
    """
    identifier = "fns_tax"
    region = "RU"
    version = "1.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        inn = payload.get("value")
        if not inn or not isinstance(inn, str):
            raise ValueError("FnsAdapter requires a valid 'value' (INN).")

        observations = []
        try:
            from atomno_mcp_fns_check.sources.egrul import EgrulClient
            from atomno_mcp_fns_check.sources.pb_fns import PbFnsClient
        except ImportError:
            raise RuntimeError("EXTERNAL_DEPENDENCY_UNAVAILABLE: atomno-mcp-fns-check not installed.")

        try:
            # Query EGRUL for basic entity status
            async with EgrulClient() as egrul_client:
                companies = await egrul_client.search_by_inn(inn)
                if companies:
                    company = companies[0]
                    observations.append({
                        "entity_type": "Company",
                        "entity_value": inn,
                        "metadata": {
                            "source": "egrul.nalog.ru",
                            "name": company.name_short or company.name_full,
                            "ogrn": company.ogrn,
                            "kpp": company.kpp,
                            "status": "liquidated" if company.liquidation_date else "active"
                        },
                        "confidence": 0.99,
                        "reliability": 0.95
                    })

            # Query Transparent Business API for tags
            async with PbFnsClient() as client:
                tags = await client.get_tags_by_inn(inn)
                if tags and (tags.has_tax_debt or tags.has_no_reporting):
                    observations.append({
                        "entity_type": "CompanyRisk",
                        "entity_value": inn,
                        "metadata": {
                            "source": "pb.nalog.ru",
                            "has_tax_debt": tags.has_tax_debt,
                            "has_no_reporting": tags.has_no_reporting
                        },
                        "confidence": 0.95,
                        "reliability": 0.90
                    })
        except Exception as e:
            raise RuntimeError(f"REQUIRES_EXTERNAL_SERVICE: FNS fetch failed: {e}")

        return observations

registry.register(FnsAdapter)
