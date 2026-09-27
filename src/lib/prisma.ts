import type { PrismaClient } from "@prisma/client";

/**
 * MERAGLYM runs against two database backends:
 *
 *  - "remote": PostgreSQL / Supabase (the production database), via
 *    `@prisma/adapter-pg`. This is the only backend in web builds.
 *  - "local":  an embedded SQLite file, via `@prisma/adapter-better-sqlite3`.
 *    Only present in the self-contained Windows desktop build, so the end user
 *    needs no external database.
 *
 * `MERAGLYM_TARGET` is inlined at build time by next.config.ts. In web builds it
 * is "web", which turns every SQLite branch below into dead code that the
 * bundler removes — web/Cloudflare bundles never contain the SQLite client or
 * its native driver.
 */

export type DbMode = "local" | "remote";

/**
 * Resolve the active database mode.
 *
 *  - Web builds: always "remote".
 *  - Desktop builds: an explicit `MERAGLYM_DB_MODE=local|remote` wins;
 *    otherwise a Postgres-style `DATABASE_URL` implies "remote"; otherwise
 *    "local" (the embedded database).
 */
export function getDbMode(): DbMode {
  if (process.env.MERAGLYM_TARGET !== "desktop") {
    return "remote";
  }

  const explicit = process.env.MERAGLYM_DB_MODE?.toLowerCase();
  if (explicit === "local" || explicit === "remote") {
    return explicit;
  }

  const url = process.env.DATABASE_URL ?? "";
  if (url.startsWith("postgres://") || url.startsWith("postgresql://")) {
    return "remote";
  }

  return "local";
}

async function createClient(): Promise<PrismaClient> {
  if (process.env.MERAGLYM_TARGET === "desktop") {
    if (getDbMode() === "local") {
      const { PrismaBetterSqlite3 } = await import(
        "@prisma/adapter-better-sqlite3"
      );
      const { PrismaClient: SqlitePrismaClient } = await import(
        "@/generated/prisma-sqlite"
      );

      // The adapter strips a leading `file:` and hands the remainder to
      // better-sqlite3, so both a raw absolute path (Windows) and a `file:` URL
      // work. The desktop shell sets MERAGLYM_SQLITE_PATH to a writable file.
      const url = process.env.MERAGLYM_SQLITE_PATH ?? "file:./meraglym.db";
      const adapter = new PrismaBetterSqlite3({ url });
      // The SQLite client is structurally identical to the pg client for every
      // model the app uses; the cast keeps a single call-site type.
      return new SqlitePrismaClient({ adapter }) as unknown as PrismaClient;
    }
  }

  const { Pool } = await import("pg");
  const { PrismaPg } = await import("@prisma/adapter-pg");
  const { PrismaClient: PgPrismaClient } = await import("@prisma/client");

  const connectionString = `${process.env.DATABASE_URL ?? ""}`;
  const pool = new Pool({ connectionString });
  const adapter = new PrismaPg(pool);
  return new PgPrismaClient({ adapter });
}

// Cache a single client per process (and survive Next.js dev hot-reload).
const globalForPrisma = globalThis as unknown as {
  meraglymPrisma?: Promise<PrismaClient>;
};

/**
 * Return the shared Prisma client for the active database mode.
 * Server-only. Always `await` this instead of importing a client directly.
 */
export function getPrisma(): Promise<PrismaClient> {
  if (!globalForPrisma.meraglymPrisma) {
    globalForPrisma.meraglymPrisma = createClient();
  }
  return globalForPrisma.meraglymPrisma;
}

export default getPrisma;
