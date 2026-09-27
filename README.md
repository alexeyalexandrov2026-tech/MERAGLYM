# MERAGLYM

MERAGLYM is an open-source-intelligence (OSINT) terminal: a Next.js 16 web app for
browsing the OSINT framework tree, full-text search, and a job/worker view, backed
by Prisma. It runs in two shapes from the same codebase:

- **Web app** — server-rendered Next.js against PostgreSQL / Supabase.
- **Windows desktop app** — a self-contained `.exe` (Electron) using an embedded
  SQLite database, requiring no Docker, Node.js, Python, or PostgreSQL on the
  end user's machine.

## Web app (development)

```bash
npm install
npm run prisma:generate      # generates both the Postgres and SQLite clients
# Point DATABASE_URL at Postgres for remote mode, e.g. via docker-compose:
docker compose up -d db
DATABASE_URL="postgresql://meraglym:meraglym_password@localhost:5432/meraglym_osint?schema=public" npm run dev
```

Open http://localhost:3000.

## Build targets and database modes

`MERAGLYM_TARGET` is read **at build time** (`next.config.ts`):

- **web** (default — `npm run build`, Docker, Cloudflare/OpenNext, CI): PostgreSQL
  only. The SQLite code path is removed as dead code, so web bundles contain no
  SQLite client or native driver. `better-sqlite3` and its Prisma adapter are
  `optionalDependencies`, so installs succeed even where they can't compile.
- **desktop** (`npm run build:next`, used by the Electron build): supports both
  backends, chosen at runtime by `src/lib/prisma.ts`:

| `MERAGLYM_DB_MODE` | Backend | Driver |
| --- | --- | --- |
| `remote` | PostgreSQL / Supabase | `@prisma/adapter-pg` |
| `local` (default) | embedded SQLite file | `@prisma/adapter-better-sqlite3` |

In a desktop build, if `MERAGLYM_DB_MODE` is unset, a `postgres://`/`postgresql://`
`DATABASE_URL` selects `remote`; otherwise `local` is used, with the database file
taken from `MERAGLYM_SQLITE_PATH`.

To use the production database from the desktop app, set `MERAGLYM_DB_MODE=remote`
and a Supabase `DATABASE_URL` in the environment the app is launched with.

## Docker (web)

```bash
docker build -t meraglym-web .
docker run -p 3000:3000 -e DATABASE_URL="postgresql://..." meraglym-web
```

The image uses Node 22 (Next.js 16 needs ≥ 20.9; Prisma 7 needs ^20.19/^22.12).

## Windows desktop app

The desktop build wraps the Next.js standalone server in Electron and ships an
embedded SQLite database seeded with the OSINT framework tree
(`public/arf.json`). The database is copied into the user's writable app-data
directory on first launch.

### Run in development

```bash
npm run dev:desktop
```

This starts `next dev` and opens an Electron window pointed at it.

### Build the installer locally (on Windows)

Requires Windows with Node.js 22, plus Python and Visual Studio Build Tools
for npm's native-module install step. Nothing is compiled: `better-sqlite3` v13
ships a prebuilt N-API binary for Windows, which loads under Electron without a
rebuild (an npm `overrides` entry makes the Prisma adapter use that same copy).

```bash
npm ci
npm run dist:win
```

The chain (`build:desktop`) runs, in order:
`prisma:generate` → `build:seeddb` (creates `resources/app.db`) →
`build:next` → `assemble:standalone` → `build:electron`, then
`electron-builder --win`.

The installer is written to `release/MERAGLYM Setup <version>.exe`.

### Build the installer via CI

The `Desktop (Windows installer)` GitHub Actions workflow builds the `.exe` on a
`windows-latest` runner. Trigger it manually (workflow_dispatch) or by pushing a
`v*` tag; the installer is uploaded as a build artifact and attached to the
release for tagged builds.

## Intelligence layer (Python)

An optional Python orchestration/ETL layer lives in `python/` (see
`python/README.md`). It is **not** bundled into the desktop app — the ETL that
populates the OSINT tree is ported to TypeScript (`src/lib/etl/ingestArf.ts`) so
the desktop build needs no Python runtime.

## Project layout

| Path | Purpose |
| --- | --- |
| `src/app` | Next.js App Router pages and API routes |
| `src/lib/prisma.ts` | Mode-aware Prisma client (SQLite / Postgres) |
| `src/lib/etl/ingestArf.ts` | TypeScript ARF tree ETL |
| `prisma/schema.prisma` | Postgres schema |
| `prisma/schema.sqlite.prisma` | SQLite schema (desktop build) |
| `electron/` | Electron main + preload |
| `scripts/build-seeddb.ts` | Builds the bundled seed SQLite database |
| `electron-builder.yml` | Windows packaging config |
