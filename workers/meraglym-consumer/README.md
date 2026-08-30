# meraglym-consumer adapters

New OSINT adapters for the deployed `meraglym-consumer` Cloudflare Worker.

## Why this exists

`meraglym.pages.dev` creates a row in the D1 `Job` table with `type` set to an
adapter id. The `meraglym-consumer` Worker consumes a queue message, looks the
id up in `AdapterRegistry`, and writes the outcome back to the row. When the id
is unknown the job is marked `FAILED` with:

```json
{ "code": "ADAPTER_NOT_FOUND", "message": "Adapter universal_recon not found" }
```

The deployed registry contains nine adapters — `phone_recon`,
`phone_person_correlator`, `egrul_registry`, `stix_ingest`, `holehe_recon`,
`fssp_check`, `opencti_connector`, `spiderfoot_meta`, `crypto_recon` — and
neither `universal_recon` nor `email_recon`, which is why both fail.

This directory adds the two missing adapters, written against the deployed
adapter contract.

- `universal_recon` — aggregator. Runs every other registered adapter whose
  `validate()` accepts the input and whose `requiredCredentials` are present in
  `env`, in parallel, then merges the entities, provenance and per-adapter
  sections into a single dossier. Adapters that cannot run are reported in
  `data.adapters_skipped` rather than failing the job.
- `email_recon` — resolves an address's MX records over Cloudflare DoH and
  attributes the provider.

`registry.ts` and `types.ts` are reconstructed from the deployed bundle so this
directory type-checks on its own (`npm run typecheck`).

## Integrating

The deployed Worker was built from a `MERAGLYM-main` checkout that is not in
this repository — the bundle's own source comments point at
`../MERAGLYM-main/src/lib/adapters/registry.ts`. To ship these adapters, copy
`universal_recon.ts` and `email_recon.ts` into that project's
`src/lib/adapters/`, import them for their registration side effect wherever the
other adapters are imported, and redeploy from there. Drop the local
`registry.ts` / `types.ts` copies in favour of that project's originals.

## Do not deploy from this directory

There is deliberately no `wrangler.toml` here. The live Worker is a **queue
consumer** with bindings that a fresh `wrangler deploy` would remove:

- D1 database binding `DB` (`meraglym-db`, `18e6b0bb-6be6-4b60-8a89-34b001531abc`)
- the Queues consumer subscription that drives `queue()`
- `nodejs_compat`
- secrets: `NUMVERIFY_API_KEY`, `DADATA_API_KEY`, `FSSP_API_KEY`,
  `OPENCTI_URL`, `OPENCTI_TOKEN`, `SPIDERFOOT_SERVER_URL`

## Known frontend bug

Two other job types failed the same way: `OSINT Framework` — a node *display
name* submitted as an adapter id — and jobs whose payload copies the target into
every field (`{"target":"Alexey Alexandrov","phone":"Alexey Alexandrov","inn":…}`).
The frontend should send a real adapter id and only populate fields it has.
