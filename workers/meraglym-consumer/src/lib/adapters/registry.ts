import type { Adapter, AdapterContext, HealthStatus } from "./types";

// Reconstructed from the deployed meraglym-consumer bundle
// (`../MERAGLYM-main/src/lib/adapters/registry.ts`) so the adapters in this
// directory type-check standalone. In MERAGLYM-main, import the real registry instead.

export interface HealthSummary {
  registered: number;
  operational: number;
  degraded: number;
  credentialRequired: number;
  unavailable: number;
  blocked: number;
  adapters: HealthStatus[];
}

export class AdapterRegistry {
  static adapters = new Map<string, Adapter>();

  static register(adapter: Adapter): void {
    this.adapters.set(adapter.id, adapter);
  }

  static get(id: string): Adapter | undefined {
    return this.adapters.get(id);
  }

  static getAll(): Adapter[] {
    return Array.from(this.adapters.values());
  }

  static async getHealthSummary(context?: AdapterContext): Promise<HealthSummary> {
    const all = this.getAll();
    const healthList = await Promise.all(
      all.map(async (adapter) => {
        try {
          return await adapter.healthCheck(context);
        } catch (err) {
          return {
            id: adapter.id,
            name: adapter.name,
            version: adapter.version,
            status: "UNAVAILABLE" as const,
            lastChecked: new Date().toISOString(),
            lastError: err instanceof Error ? err.message : "Health check threw an unhandled error",
            category: adapter.category,
            requiredCredentials: adapter.requiredCredentials,
          };
        }
      }),
    );

    let operational = 0;
    let degraded = 0;
    let credentialRequired = 0;
    let unavailable = 0;
    let blocked = 0;
    for (const h of healthList) {
      if (h.status === "OPERATIONAL") operational++;
      else if (h.status === "DEGRADED") degraded++;
      else if (h.status === "CREDENTIAL_REQUIRED") credentialRequired++;
      else if (h.status === "UNAVAILABLE") unavailable++;
      else if (h.status === "BLOCKED" || h.status === "TIMEOUT") blocked++;
    }

    return { registered: all.length, operational, degraded, credentialRequired, unavailable, blocked, adapters: healthList };
  }
}
