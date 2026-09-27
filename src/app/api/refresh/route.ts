import { NextResponse } from "next/server";
import { getPrisma } from "@/lib/prisma";
import { ingestArf, type PrismaNodeClient } from "@/lib/etl/ingestArf";

export const dynamic = "force-dynamic";

/**
 * Re-ingest the OSINT framework tree into the database. Defaults to the bundled
 * offline snapshot (public/arf.json); pass ?source=<url|path> to override.
 */
export async function POST(request: Request) {
  try {
    const url = new URL(request.url);
    const source = url.searchParams.get("source") ?? undefined;

    const prisma = await getPrisma();
    const result = await ingestArf(prisma as unknown as PrismaNodeClient, {
      source,
    });

    return NextResponse.json({ status: "ok", ...result });
  } catch (error) {
    console.error("Error refreshing sources:", error);
    return NextResponse.json(
      { error: "Internal Server Error" },
      { status: 500 },
    );
  }
}
