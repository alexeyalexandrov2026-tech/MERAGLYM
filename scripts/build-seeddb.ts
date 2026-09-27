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

  // Forward slashes work for SQLite/Prisma on every OS and avoid backslash
  // escaping issues in the URL on Windows.
  const dbUrl = `file:${dbPath.split(path.sep).join("/")}`;

  console.log(`Creating schema in ${dbPath} ...`);
  // Run the Prisma CLI entry script with the current Node binary instead of
  // spawning `npx`: on Windows, Node refuses to spawn `.cmd` shims without a
  // shell (CVE-2024-27980 hardening), and this avoids shell quoting entirely.
  const prismaCli = path.join(root, "node_modules", "prisma", "build", "index.js");
  execFileSync(
    process.execPath,
    [
      prismaCli,
      "db",
      "push",
      "--schema",
      "prisma/schema.sqlite.prisma",
      "--url",
      dbUrl,
    ],
    { stdio: "inherit" },
  );

  const adapter = new PrismaBetterSqlite3({ url: dbUrl });
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
