import { promises as fs } from "fs";
import path from "path";

/**
 * TypeScript port of python/meraglym/etl/ingest_arf.py.
 *
 * Recursively ingests the OSINT framework tree (arf.json) into the `Node`
 * table, upserting by (name, parentId) so re-running is idempotent. Used both
 * by the desktop seed-database build and by the in-app "refresh sources" route,
 * which removes the need to bundle a Python runtime.
 */

export interface ArfNode {
  name: string;
  type?: string;
  url?: string;
  description?: string;
  status?: string;
  pricing?: string;
  bestFor?: string;
  input?: string;
  output?: string;
  opsec?: string;
  opsecNote?: string;
  localInstall?: boolean;
  googleDork?: boolean;
  registration?: boolean;
  editUrl?: boolean;
  api?: boolean;
  invitationOnly?: boolean;
  deprecated?: boolean;
  children?: ArfNode[];
}

/** The Node create payload (parentId supplied separately by the walker). */
interface NodeData {
  name: string;
  parentId: number | null;
  type: string;
  url: string | null;
  description: string | null;
  status: string | null;
  pricing: string | null;
  bestFor: string | null;
  input: string | null;
  output: string | null;
  opsec: string | null;
  opsecNote: string | null;
  localInstall: boolean | null;
  googleDork: boolean | null;
  registration: boolean | null;
  editUrl: boolean | null;
  api: boolean | null;
  invitationOnly: boolean | null;
  deprecated: boolean | null;
}

interface NodeRecord {
  id: number;
}

/**
 * Minimal structural view of the parts of the Prisma client this module needs.
 * Both the Postgres and SQLite generated clients satisfy it; call sites pass
 * their client with a cast.
 */
export interface PrismaNodeClient {
  node: {
    findFirst(args: {
      where: { name: string; parentId: number | null };
      select: { id: true };
    }): Promise<NodeRecord | null>;
    create(args: { data: NodeData }): Promise<NodeRecord>;
    update(args: {
      where: { id: number };
      data: Omit<NodeData, "parentId">;
    }): Promise<NodeRecord>;
  };
}

export interface IngestOptions {
  /** URL (http/https) or filesystem path. Defaults to the bundled snapshot. */
  source?: string;
}

export interface IngestResult {
  inserted: number;
  updated: number;
  total: number;
}

function resolveType(node: ArfNode): string {
  if (node.type) return node.type;
  return node.children && node.children.length > 0 ? "folder" : "url";
}

function toNodeData(node: ArfNode, parentId: number | null): NodeData {
  return {
    name: node.name,
    parentId,
    type: resolveType(node),
    url: node.url ?? null,
    description: node.description ?? null,
    status: node.status ?? null,
    pricing: node.pricing ?? null,
    bestFor: node.bestFor ?? null,
    input: node.input ?? null,
    output: node.output ?? null,
    opsec: node.opsec ?? null,
    opsecNote: node.opsecNote ?? null,
    localInstall: node.localInstall ?? null,
    googleDork: node.googleDork ?? null,
    registration: node.registration ?? null,
    editUrl: node.editUrl ?? null,
    api: node.api ?? null,
    invitationOnly: node.invitationOnly ?? null,
    deprecated: node.deprecated ?? null,
  };
}

/** The default bundled snapshot lives in the app's public directory. */
export function defaultArfPath(): string {
  return path.join(process.cwd(), "public", "arf.json");
}

async function loadArf(source: string): Promise<ArfNode[]> {
  let raw: string;
  if (source.startsWith("http://") || source.startsWith("https://")) {
    const res = await fetch(source);
    if (!res.ok) {
      throw new Error(`Failed to download arf.json: ${res.status} ${res.statusText}`);
    }
    raw = await res.text();
  } else {
    raw = await fs.readFile(source, "utf-8");
  }

  const data = JSON.parse(raw) as ArfNode | ArfNode[];
  return Array.isArray(data) ? data : [data];
}

/**
 * Ingest the arf.json tree into the Node table via the provided Prisma client.
 * Upserts by (name, parentId) so it is safe to run repeatedly.
 */
export async function ingestArf(
  prisma: PrismaNodeClient,
  opts: IngestOptions = {},
): Promise<IngestResult> {
  const source = opts.source ?? defaultArfPath();
  const roots = await loadArf(source);

  const result: IngestResult = { inserted: 0, updated: 0, total: 0 };

  const walk = async (node: ArfNode, parentId: number | null): Promise<void> => {
    result.total += 1;
    const data = toNodeData(node, parentId);

    const existing = await prisma.node.findFirst({
      where: { name: node.name, parentId },
      select: { id: true },
    });

    let nodeId: number;
    if (existing) {
      const { parentId: _parentId, ...updateData } = data;
      void _parentId;
      await prisma.node.update({ where: { id: existing.id }, data: updateData });
      nodeId = existing.id;
      result.updated += 1;
    } else {
      const created = await prisma.node.create({ data });
      nodeId = created.id;
      result.inserted += 1;
    }

    if (node.children && node.children.length > 0) {
      for (const child of node.children) {
        await walk(child, nodeId);
      }
    }
  };

  for (const root of roots) {
    await walk(root, null);
  }

  return result;
}
