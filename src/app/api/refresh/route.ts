import { NextResponse } from "next/server";
import { getPrisma } from "@/lib/prisma";
import { ingestArf, type PrismaNodeClient } from "@/lib/etl/ingestArf";
import { checkAdmin } from "@/lib/jobsAuth";

export const dynamic = "force-dynamic";

/**
 * Re-ingest the OSINT framework tree into the database (admin only: same
 * JOBS_ADMIN_TOKEN as /api/jobs, header `x-admin-token`). Defaults to the
 * bundled snapshot (public/arf.json); `?source=<https URL>` overrides it.
 * Local file paths are not accepted from the network.
 */
export async function POST(request: Request) {
  const auth = checkAdmin(request);
  if (auth === "disabled") {
    return NextResponse.json({ error: "Refresh is disabled (JOBS_ADMIN_TOKEN not configured)" }, { status: 503 });
  }
  if (auth === "locked") {
    return NextResponse.json({ error: "Too many failed attempts, try again later" }, { status: 429 });
  }
  if (auth !== "ok") {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const url = new URL(request.url);
    const source = url.searchParams.get("source") ?? undefined;
    if (source !== undefined && !/^https:\/\/[^\s]+$/.test(source)) {
      return NextResponse.json({ error: "source must be an https:// URL" }, { status: 400 });
    }

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
