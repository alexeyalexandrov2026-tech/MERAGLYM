// Mirrors the adapter contract already implemented in MERAGLYM-main/src/lib/adapters/registry.ts,
// reconstructed from the deployed meraglym-consumer bundle so new adapters can be written against it.

export interface AdapterContext {
  env: Record<string, unknown>;
  requestId: string;
}

export interface AdapterInput {
  target?: string;
  email?: string;
  phone?: string;
  inn?: string;
  address?: string;
  [key: string]: unknown;
}

export type SourceType = "LOCAL_ENRICHMENT" | "LIVE_EXTERNAL_SOURCE" | "EXTERNAL_REFERENCE";

export interface Provenance {
  sourceId: string;
  sourceType: SourceType;
  url?: string;
  adapter: string;
  adapterVersion: string;
  retrievedAt: string;
  requestId: string;
  verified: boolean;
}

export interface Entity {
  type: string;
  value: string;
  confidence: number;
}

export interface AdapterResult {
  success: boolean;
  adapter: string;
  adapterVersion: string;
  startedAt: string;
  completedAt: string;
  verified: boolean;
  data: Record<string, unknown>;
  observations: unknown[];
  entities: Entity[];
  relationships: unknown[];
  source: Provenance[];
  confidence: number;
}

export type HealthState =
  | "OPERATIONAL"
  | "DEGRADED"
  | "CREDENTIAL_REQUIRED"
  | "UNAVAILABLE"
  | "BLOCKED"
  | "TIMEOUT";

export interface HealthStatus {
  id: string;
  name: string;
  version: string;
  status: HealthState;
  latencyMs?: number;
  lastChecked: string;
  lastError?: string;
  requiredCredentials: string[];
  category: string;
}

export interface Adapter {
  id: string;
  name: string;
  version: string;
  category: string;
  requiredCredentials: string[];
  validate: (input: AdapterInput) => void;
  healthCheck: (ctx?: AdapterContext) => Promise<HealthStatus>;
  execute: (input: AdapterInput, ctx: AdapterContext) => Promise<AdapterResult>;
}
