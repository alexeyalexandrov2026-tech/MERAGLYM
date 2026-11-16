# MERAGLYM Intelligence Layer (Python)

The Python orchestration layer runs the ETL that ingests the OSINT framework
tree into PostgreSQL and hosts the OSINT adapters executed by the job worker.

## Requirements

- Python `>=3.11` (managed via [`uv`](https://github.com/astral-sh/uv))
- A PostgreSQL database reachable via `DATABASE_URL`

## Setup

```bash
uv sync
```

## Environment

- `DATABASE_URL` — PostgreSQL connection string. A Prisma-style
  `?schema=public` suffix is accepted and automatically translated to the
  libpq `search_path` option, so the same value works for both the Next.js
  (Prisma) layer and this Python layer.

## Running

```bash
# Ingest the OSINT framework tree (defaults to the upstream arf.json URL)
uv run python -m meraglym.etl.ingest_arf

# Start the job worker (polls the Job table)
uv run python -m meraglym.etl.worker

# Run the test suite
uv run pytest

# Run the adapter end-to-end smoke test
uv run python e2e_test.py
```

## Adapter configuration

Most adapters degrade gracefully when their dependency is missing. Several
adapters shell out to external OSINT tools; point them at the installed tool
via an environment variable (or, where noted, place the tool on `PATH`).
When the variable is unset and the tool is not on `PATH`, the adapter reports
`EXTERNAL_DEPENDENCY_UNAVAILABLE` instead of failing hard.

| Adapter | Env var | Points to |
| :--- | :--- | :--- |
| `camera_recon` | `CCTVSCAN_PATH` | CCTV-scanner `latest.py` |
| `darkweb_mapper` | `TORBOT_PATH` | TorBot `main.py` |
| `geospatial_mapper` | `GEOWIFI_PATH` | GeoWiFi `geowifi.py` (or add `geowifi` to `PATH`) |
| `social_recon` | `SOCIAL_ANALYZER_PATH` | Social Analyzer `app.py` (Maigret is auto-detected on `PATH`) |
| `spiderfoot_meta` | `SPIDERFOOT_PATH` | SpiderFoot `sf.py` |

Credential-gated adapters read their secrets from the environment:

`ETHERSCAN_API_KEY` (or `BLOCKCHAIN_API_KEY`) for Ethereum in `crypto_recon`, `OPENCTI_URL` + `OPENCTI_TOKEN` (`opencti_connector`),
and a valid GHunt session (`email_recon`).

## Adapters and worker-host setup

All 19 adapters are registered when `meraglym.osint` is imported (the worker does
this). An adapter whose tool, library or credential is missing fails the job
immediately with a classified error instead of retrying:

- `EXTERNAL_DEPENDENCY_UNAVAILABLE: …` — tool/library not installed or not configured;
- `REQUIRES_USER_CREDENTIAL: …` — an API key / session is needed;
- `GEO_BLOCKED: …` — a Russian registry is unreachable and no `RU_PROXY_URL` is set;
- `REQUIRES_EXTERNAL_SERVICE: …` — upstream unreachable (outage, rate limit, proxy failure);
  these are retried with backoff.

| Adapter | Input | Needs on the worker host |
| :--- | :--- | :--- |
| `egrul_registry`, `fns_tax`, `efrsb_bankruptcy`, `fssp_check`, `kad_arbitr` | INN (OGRN for EGRUL) | `atomno-mcp-fns-check` (dependency) + Russian IP or `RU_PROXY_URL` |
| `rfsd_financials`, `sudrf_courts`, `mvd_wanted` | INN / name | Russian IP or `RU_PROXY_URL` |
| `holehe_recon` | email | `holehe` on `PATH` / `MERAGLYM_TOOLS_BIN` |
| `social_recon` | username | `maigret` and/or `social-analyzer` on `PATH` |
| `email_recon` | email | `ghunt` + a session (`ghunt login` as the worker user) |
| `geospatial_mapper` | BSSID / SSID | `GEOWIFI_PATH` → `geowifi.py` (keys for WiGLE/Google/Combain optional) |
| `metadata_extractor` | image URL / upload name | `exifread` (dependency); uploads in `METADATA_UPLOAD_DIR` |
| `crypto_recon` | BTC / ETH address | BTC keyless (Esplora); ETH needs `ETHERSCAN_API_KEY` |
| `camera_recon` | IP / CIDR ≤ /24 | `CCTVSCAN_PATH` → CCTV-scanner `latest.py`; public IPs need `CAMERA_SCAN_ALLOW_PUBLIC=1` |
| `darkweb_mapper` | v3 .onion URL | `TORBOT_PATH` → TorBot `main.py` + tor SOCKS (`TOR_SOCKS_HOST`/`PORT`) |
| `spiderfoot_meta` | domain / IP | `SPIDERFOOT_PATH` → `sf.py` |
| `opencti_connector` | indicator | `OPENCTI_URL` + `OPENCTI_TOKEN` |
| `stix_ingest` | STIX objects | — |

Script-based tools are run with a `.venv/bin/python` found next to the script
(or `<TOOL>_PYTHON`, e.g. `SPIDERFOOT_PYTHON`), so each tool keeps its own
dependencies. The worker keeps a single database connection open and
reconnects with backoff if it drops.
