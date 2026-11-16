import builtins

import pytest

from meraglym.osint.general.stix import StixAdapter
from meraglym.osint.cis.rfsd import RfsdAdapter
from meraglym.osint.cis.egrul import EgrulAdapter


@pytest.mark.asyncio
async def test_stix_adapter():
    adapter = StixAdapter()
    payload = {
        "objects": [
            {
                "type": "threat-actor",
                "id": "threat-actor--12345",
                "name": "APT28",
                "aliases": ["Fancy Bear", "Sednit"]
            }
        ]
    }

    observations = await adapter.execute(payload)
    assert len(observations) == 1
    obs = observations[0]
    assert obs["entity_type"] == "ThreatActor"
    assert obs["entity_value"] == "APT28"
    assert "Fancy Bear" in obs["metadata"]["aliases"]
    assert obs["confidence"] == 0.90


@pytest.mark.asyncio
async def test_rfsd_adapter_requires_inn():
    # A missing INN must raise a ValueError before any network access.
    adapter = RfsdAdapter()

    with pytest.raises(ValueError, match="inn"):
        await adapter.execute({})


@pytest.mark.asyncio
async def test_egrul_adapter_without_library(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("atomno_mcp_fns_check"):
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(RuntimeError, match="EXTERNAL_DEPENDENCY_UNAVAILABLE"):
        await EgrulAdapter().execute({"value": "7736050003"})
