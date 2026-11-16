"""Every adapter must be registered and must fail with a classified error when its
dependency / credential is missing (never "not found in registry")."""
import pytest

import meraglym.osint as osint
from meraglym.osint import ALL_ADAPTER_IDENTIFIERS, registry
from meraglym.etl import worker

TOOL_ENV = ["SPIDERFOOT_PATH", "TORBOT_PATH", "GEOWIFI_PATH", "CCTVSCAN_PATH", "SOCIAL_ANALYZER_PATH",
            "MAIGRET_PATH", "HOLEHE_PATH", "GHUNT_PATH", "MERAGLYM_TOOLS_BIN", "OPENCTI_URL", "OPENCTI_TOKEN",
            "ETHERSCAN_API_KEY", "BLOCKCHAIN_API_KEY"]


def test_all_19_adapters_registered():
    assert len(ALL_ADAPTER_IDENTIFIERS) == 19
    assert set(registry.identifiers()) == set(ALL_ADAPTER_IDENTIFIERS)
    for ident in ALL_ADAPTER_IDENTIFIERS:
        assert registry.get_adapter(ident).identifier == ident


def test_worker_imports_full_registry():
    assert set(ALL_ADAPTER_IDENTIFIERS) <= set(registry.identifiers())
    assert worker.meraglym.osint is osint


def test_unknown_adapter_is_permanent_error():
    with pytest.raises(ValueError) as e:
        registry.get_adapter("nope")
    assert worker._is_permanent(e.value)


def test_reregistering_same_class_is_idempotent():
    cls = type(registry.get_adapter("stix_ingest"))
    registry.register(cls)
    assert registry.get_adapter("stix_ingest")


@pytest.fixture
def bare_env(monkeypatch, tmp_path):
    for k in TOOL_ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))  # no external binaries
    monkeypatch.setenv("GHUNT_CREDS_PATH", str(tmp_path / "missing-creds"))


CASES = [
    ("holehe_recon", {"value": "a@example.com"}, "EXTERNAL_DEPENDENCY_UNAVAILABLE"),
    ("social_recon", {"value": "example_user"}, "EXTERNAL_DEPENDENCY_UNAVAILABLE"),
    ("email_recon", {"value": "a@example.com"}, "EXTERNAL_DEPENDENCY_UNAVAILABLE"),
    ("geospatial_mapper", {"value": "00:0C:42:1F:65:E9"}, "EXTERNAL_DEPENDENCY_UNAVAILABLE"),
    ("spiderfoot_meta", {"value": "example.com"}, "EXTERNAL_DEPENDENCY_UNAVAILABLE"),
    ("darkweb_mapper", {"value": "http://" + "a" * 56 + ".onion"}, "EXTERNAL_DEPENDENCY_UNAVAILABLE"),
    ("camera_recon", {"value": "127.0.0.1"}, "EXTERNAL_DEPENDENCY_UNAVAILABLE"),
    ("opencti_connector", {"value": "1.2.3.4"}, "REQUIRES_USER_CREDENTIAL"),
    ("crypto_recon", {"value": "0x" + "1" * 40}, "REQUIRES_USER_CREDENTIAL"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("ident,payload,prefix", CASES)
async def test_missing_dependency_is_classified(bare_env, ident, payload, prefix):
    with pytest.raises(RuntimeError) as e:
        await registry.get_adapter(ident).execute(payload)
    assert str(e.value).startswith(prefix)
    assert worker._is_permanent(e.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("ident", ["egrul_registry", "fns_tax", "efrsb_bankruptcy", "fssp_check", "kad_arbitr",
                                   "rfsd_financials"])
async def test_ru_registries_validate_inn(ident):
    with pytest.raises(ValueError, match="INVALID_INPUT"):
        await registry.get_adapter(ident).execute({"value": "not-an-inn"})


@pytest.mark.asyncio
async def test_camera_refuses_public_targets(monkeypatch):
    monkeypatch.delenv("CAMERA_SCAN_ALLOW_PUBLIC", raising=False)
    with pytest.raises(ValueError, match="public"):
        await registry.get_adapter("camera_recon").execute({"value": "8.8.8.8"})


@pytest.mark.asyncio
async def test_metadata_rejects_paths_outside_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("METADATA_UPLOAD_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="INVALID_INPUT"):
        await registry.get_adapter("metadata_extractor").execute({"value": "../../etc/passwd"})


class _Cur:
    def __init__(self, row):
        self.row, self.queries, self.params = row, [], []

    def execute(self, q, p=None):
        self.queries.append(q)
        self.params.append(p)

    def fetchone(self):
        return self.row

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


class _Conn:
    def __init__(self, row=None):
        self.cur, self.rolled, self.committed = _Cur(row), 0, 0

    def cursor(self):
        return self.cur

    def rollback(self):
        self.rolled += 1

    def commit(self):
        self.committed += 1


def test_idle_poll_ends_transaction():
    conn = _Conn(row=None)
    assert worker.claim_and_process(conn) is False
    assert conn.rolled == 1


def test_permanent_error_marks_failed_without_retry():
    conn = _Conn()
    worker.process_job(conn, 9, "run_adapter", {"adapter_identifier": "does_not_exist"}, 0, 3)
    # the failure UPDATE sets status FAILED immediately (no RETRY for unknown adapters)
    assert conn.cur.params[-1][0] == "FAILED"
    assert "not found in registry" in conn.cur.params[-1][1]


def test_ru_geo_block_without_proxy_is_permanent(monkeypatch):
    from meraglym.osint._util import ru_service_error
    monkeypatch.delenv("RU_PROXY_URL", raising=False)
    err = ru_service_error("kad.arbitr.ru", Exception("451"))
    assert str(err).startswith("GEO_BLOCKED") and worker._is_permanent(err)
    monkeypatch.setenv("RU_PROXY_URL", "socks5://127.0.0.1:1")
    err = ru_service_error("kad.arbitr.ru", Exception("timeout"))
    assert str(err).startswith("REQUIRES_EXTERNAL_SERVICE") and not worker._is_permanent(err)


def test_assert_public_url_blocks_internal_hosts():
    import pytest
    from meraglym.osint._util import assert_public_url

    for url in ("http://127.0.0.1:8787/", "http://169.254.169.254/metadata", "http://10.0.0.4/", "file:///etc/passwd", "http://localhost/"):
        with pytest.raises(ValueError):
            assert_public_url(url)


def test_argv_option_injection_rejected():
    import asyncio
    import pytest
    from meraglym.osint.general.social import SocialMediaAdapter
    from meraglym.osint.general.holehe import HoleheAdapter

    with pytest.raises(ValueError):
        asyncio.run(SocialMediaAdapter().execute({"value": "--db"}))
    with pytest.raises(ValueError):
        asyncio.run(HoleheAdapter().execute({"value": "-x@example.com"}))


def test_run_tool_killed_on_outer_cancel():
    import asyncio
    import os
    import sys
    import time
    from meraglym.osint._util import run_tool

    marker = f"/tmp/meraglym-runtool-{os.getpid()}"

    async def main():
        try:
            await asyncio.wait_for(
                run_tool([sys.executable, "-c", f"import time; time.sleep(1.5); open('{marker}','w').write('x')"], timeout=60),
                timeout=0.3,
            )
        except asyncio.TimeoutError:
            pass

    asyncio.run(main())
    time.sleep(2)
    assert not os.path.exists(marker)
