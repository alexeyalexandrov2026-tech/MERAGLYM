import os
from typing import Any, Dict, List

from meraglym.osint import BaseAdapter, registry
from meraglym.osint._util import credential_error, service_error

QUERY = """
query Search($search: String!, $first: Int) {
  stixCyberObservables(search: $search, first: $first) {
    edges { node { id entity_type observable_value created_at x_opencti_score
      objectLabel { value } } }
  }
}
"""


class OpenCTIAdapter(BaseAdapter):
    """Search an OpenCTI instance for observables (IP, domain, hash, email...) via GraphQL.

    Needs OPENCTI_URL (e.g. https://opencti.example.org) and OPENCTI_TOKEN (user API token).
    """
    identifier = "opencti_connector"
    region = "GLOBAL"
    version = "2.0.0"

    async def execute(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        value = str(payload.get("value") or "").strip()
        if not value:
            raise ValueError("INVALID_INPUT: opencti_connector requires an indicator in 'value'.")
        url, token = os.environ.get("OPENCTI_URL"), os.environ.get("OPENCTI_TOKEN")
        if not url or not token:
            raise credential_error("set OPENCTI_URL and OPENCTI_TOKEN (OpenCTI profile -> API access).")
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30.0) as c:
                r = await c.post(f"{url.rstrip('/')}/graphql",
                                 json={"query": QUERY, "variables": {"search": value, "first": 25}},
                                 headers={"Authorization": f"Bearer {token}"})
            if r.status_code in (401, 403):
                raise credential_error("OpenCTI rejected the token.")
            r.raise_for_status()
            data = r.json()
        except RuntimeError:
            raise
        except Exception as e:
            raise service_error(f"OpenCTI error: {e}")
        if data.get("errors"):
            raise service_error(f"OpenCTI GraphQL error: {data['errors'][0].get('message')}")
        edges = (((data.get("data") or {}).get("stixCyberObservables") or {}).get("edges")) or []
        return [{
            "entity_type": e["node"].get("entity_type") or "Observable",
            "entity_value": e["node"].get("observable_value"),
            "metadata": {"source": "opencti", "id": e["node"].get("id"), "score": e["node"].get("x_opencti_score"),
                         "labels": [l.get("value") for l in e["node"].get("objectLabel") or []],
                         "created_at": e["node"].get("created_at")},
            "confidence": 0.9,
            "reliability": 0.85,
        } for e in edges if e.get("node")]


registry.register(OpenCTIAdapter)
