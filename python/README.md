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
| `camera_recon` | `CCTVSCAN_PATH` | `cctvscan` binary (or add it to `PATH`) |
| `darkweb_mapper` | `TORBOT_PATH` | TorBot `main.py` |
| `geospatial_mapper` | `GEOWIFI_PATH` | GeoWiFi `geowifi.py` (or add `geowifi` to `PATH`) |
| `social_recon` | `SOCIAL_ANALYZER_PATH` | Social Analyzer `app.py` (Maigret is auto-detected on `PATH`) |
| `spiderfoot_meta` | `SPIDERFOOT_PATH` | SpiderFoot `sf.py` |

Credential-gated adapters read their secrets from the environment:
`BLOCKCHAIN_API_KEY` (`crypto_recon`), `OPENCTI_TOKEN` (`opencti_connector`),
and a valid GHunt session (`email_recon`).
