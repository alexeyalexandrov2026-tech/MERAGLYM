import { AdapterRegistry } from "./registry";
import type { Adapter, AdapterContext, AdapterInput, AdapterResult, Entity, Provenance } from "./types";

const ID = "universal_recon";
const VERSION = "1.0.0";

function hasCredentials(adapter: Adapter, env: Record<string, unknown>): boolean {
  return adapter.requiredCredentials.every((key) => Boolean(env?.[key]));
}

function accepts(adapter: Adapter, input: AdapterInput): boolean {
  try {
    adapter.validate(input);
    return true;
  } catch {
    return false;
  }
}

interface Skipped {
  adapter: string;
  reason: string;
}

AdapterRegistry.register({
  id: ID,
  name: "Universal Reconnaissance (Cross-Adapter Aggregator)",
  version: VERSION,
  category: "global_recon",
  requiredCredentials: [],
  validate: (input) => {
    if (!input?.target && !input?.email && !input?.phone && !input?.inn) {
      throw new Error("A target, email, phone or inn is required");
    }
  },
  healthCheck: async () => ({
    id: ID,
    name: "Universal Reconnaissance (Cross-Adapter Aggregator)",
    version: VERSION,
    status: "OPERATIONAL",
    latencyMs: 0,
    lastChecked: new Date().toISOString(),
    requiredCredentials: [],
    category: "global_recon",
  }),
  execute: async (input: AdapterInput, ctx: AdapterContext): Promise<AdapterResult> => {
    const started = new Date().toISOString();
    const env = (ctx.env ?? {}) as Record<string, unknown>;

    const candidates: Adapter[] = [];
    const skipped: Skipped[] = [];

    for (const adapter of AdapterRegistry.getAll() as Adapter[]) {
      if (adapter.id === ID) continue;
      if (!hasCredentials(adapter, env)) {
        skipped.push({ adapter: adapter.id, reason: "MISSING_CREDENTIALS" });
        continue;
      }
      if (!accepts(adapter, input)) {
        skipped.push({ adapter: adapter.id, reason: "INPUT_NOT_APPLICABLE" });
        continue;
      }
      candidates.push(adapter);
    }

    const settled = await Promise.allSettled(
      candidates.map((adapter) => adapter.execute(input, { ...ctx, requestId: `${ctx.requestId}:${adapter.id}` })),
    );

    const entities: Entity[] = [];
    const source: Provenance[] = [];
    const observations: unknown[] = [];
    const relationships: unknown[] = [];
    const sections: Record<string, unknown> = {};
    const failed: Skipped[] = [];

    settled.forEach((outcome, i) => {
      const adapter = candidates[i];
      if (outcome.status === "rejected") {
        failed.push({
          adapter: adapter.id,
          reason: outcome.reason instanceof Error ? outcome.reason.message : String(outcome.reason),
        });
        return;
      }
      const result = outcome.value;
      sections[adapter.id] = result.data;
      entities.push(...result.entities);
      source.push(...result.source);
      observations.push(...result.observations);
      relationships.push(...result.relationships);
    });

    const succeeded = candidates.length - failed.length;
    const verified = source.some((s) => s.verified);

    // Deduplicate entities that several adapters independently reported.
    const seen = new Set<string>();
    const mergedEntities = entities.filter((entity) => {
      const key = `${entity.type}:${entity.value}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    return {
      success: true,
      adapter: ID,
      adapterVersion: VERSION,
      startedAt: started,
      completedAt: new Date().toISOString(),
      verified,
      data: {
        target: input.target ?? input.email ?? input.phone ?? input.inn ?? "",
        adapters_run: candidates.map((a) => a.id),
        adapters_succeeded: succeeded,
        adapters_failed: failed,
        adapters_skipped: skipped,
        sections,
      },
      observations,
      entities: mergedEntities,
      relationships,
      source: [
        ...source,
        {
          sourceId: "src_universal_recon_aggregator",
          sourceType: verified ? "LIVE_EXTERNAL_SOURCE" : "LOCAL_ENRICHMENT",
          adapter: ID,
          adapterVersion: VERSION,
          retrievedAt: started,
          requestId: ctx.requestId,
          verified,
        },
      ],
      confidence: succeeded === 0 ? 0.1 : verified ? 0.95 : 0.8,
    };
  },
});
