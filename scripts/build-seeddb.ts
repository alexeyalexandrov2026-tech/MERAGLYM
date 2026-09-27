/**
 * Build the seed SQLite database bundled with the desktop app.
 *
 *   1. Create a fresh resources/app.db from prisma/schema.sqlite.prisma.
 *   2. Ingest the OSINT framework tree from the bundled public/arf.json.
 *
 * The resulting file is shipped read-only in the installer and copied into the
 * user's writable app-data directory on first launch.
 *
 * Run: npm run build:seeddb
 */
import { promises as fs } from "fs";
import path from "path";
import { execFileSync } from "child_process";
import { PrismaClient } from "../src/generated/prisma-sqlite";
import { PrismaBetterSqlite3 } from "@prisma/adapter-better-sqlite3";
import { ingestArf, type PrismaNodeClient } from "../src/lib/etl/ingestArf";

async function main(): Promise<void> {
  const root = process.cwd();
  const resourcesDir = path.join(root, "resources");
  const dbPath = path.join(resourcesDir, "app.db");

  await fs.mkdir(resourcesDir, { recursive: true });
  // Start from a clean file so `db push` never needs data-loss confirmation.
  await fs.rm(dbPath, { force: true });

  console.log(`Creating schema in ${dbPath} ...`);
  const npx = process.platform === "win32" ? "npx.cmd" : "npx";
  execFileSync(
    npx,
    [
      "prisma",
      "db",
      "push",
      "--schema",
      "prisma/schema.sqlite.prisma",
      "--url",
      `file:${dbPath}`,
    ],
    { stdio: "inherit" },
  );

  const adapter = new PrismaBetterSqlite3({ url: `file:${dbPath}` });
  const prisma = new PrismaClient({ adapter });
  try {
    console.log("Ingesting OSINT framework tree from public/arf.json ...");
    const result = await ingestArf(prisma as unknown as PrismaNodeClient, {
      source: path.join(root, "public", "arf.json"),
    });
    console.log(
      `Seed DB ready: ${result.inserted} inserted, ${result.updated} updated, ${result.total} total nodes.`,
    );
  } finally {
    await prisma.$disconnect();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
