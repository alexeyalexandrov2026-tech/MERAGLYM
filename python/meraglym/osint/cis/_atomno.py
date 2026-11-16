"""Thin glue around the ``atomno-mcp-fns-check`` clients (EGRUL, PB FNS, EFRSB, FSSP, KAD)."""
from __future__ import annotations

import dataclasses
from typing import Any

from meraglym.osint._util import dependency_error, ru_http_client, ru_service_error


def import_client(module: str, name: str):
    try:
        mod = __import__(f"atomno_mcp_fns_check.sources.{module}", fromlist=[name])
        return getattr(mod, name)
    except ImportError:
        raise dependency_error("atomno-mcp-fns-check not installed (pip install atomno-mcp-fns-check).")


async def call(source: str, module: str, client_name: str, method: str, *args):
    """Instantiate ``client_name`` with a proxy-aware httpx client and call ``method``."""
    cls = import_client(module, client_name)
    try:
        async with ru_http_client(timeout=30.0) as http:
            async with cls(client=http) as client:
                return await getattr(client, method)(*args)
    except RuntimeError as e:
        if str(e).startswith(("EXTERNAL_DEPENDENCY_UNAVAILABLE", "REQUIRES_", "GEO_BLOCKED")):
            raise
        raise ru_service_error(source, e)
    except Exception as e:  # network errors, 403 geo-blocks, parsing changes
        raise ru_service_error(source, e)


def to_dict(obj: Any) -> dict:
    if dataclasses.is_dataclass(obj):
        d = dataclasses.asdict(obj)
        d.pop("raw", None)
        return d
    return dict(obj) if isinstance(obj, dict) else {"value": str(obj)}
