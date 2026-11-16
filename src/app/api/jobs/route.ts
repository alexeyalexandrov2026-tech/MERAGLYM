import { NextResponse } from "next/server";
import type { Prisma } from "@prisma/client";
import { getPrisma } from "@/lib/prisma";
import { buildJobPayload } from "@/lib/jobAdapters";
import { checkAdmin } from "@/lib/jobsAuth";

export const dynamic = "force-dynamic";

const RATE_PER_MINUTE = Number(process.env.JOBS_RATE_PER_MINUTE ?? 10);
const MAX_QUEUED = Number(process.env.JOBS_MAX_QUEUED ?? 50);

/**
 * List the 50 most recently updated jobs. Without a valid admin token only
 * status metadata is returned; payloads, results and errors (which can contain
 * personal data) require the token.
 */
export async function GET(request: Request) {
  try {
    const auth = checkAdmin(request, { countFailures: false });
    const authorized = auth === "ok";
    const prisma = await getPrisma();
    const jobs = await prisma.job.findMany({
      orderBy: {
        updatedAt: "desc",
      },
      take: 50,
    });

    if (authorized) {
      return NextResponse.json(jobs, { headers: { "cache-control": "no-store" } });
    }
    const redacted = jobs.map((job) => ({
      id: job.id,
      type: job.type,
      status: job.status,
      payload: null,
      result: null,
      error: job.error ? "[hidden — admin token required]" : null,
      startedAt: job.startedAt,
      completedAt: job.completedAt,
      retryCount: job.retryCount,
      maxRetries: job.maxRetries,
      createdAt: job.createdAt,
      updatedAt: job.updatedAt,
      redacted: true,
    }));
    return NextResponse.json(redacted, {
      headers: { "cache-control": "no-store", "x-admin-auth": auth },
    });
  } catch (error) {
    console.error("Error fetching jobs:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}

/**
 * Queue an OSINT adapter run for the Python worker.
 * Body: { "adapter": "<identifier>", "target": "<value>" }
 * Header: x-admin-token: <JOBS_ADMIN_TOKEN>
 */
export async function POST(request: Request) {
  const auth = checkAdmin(request);
  if (auth === "disabled") {
    return NextResponse.json({ error: "Job creation is disabled (JOBS_ADMIN_TOKEN not configured)" }, { status: 503 });
  }
  if (auth === "locked") {
    return NextResponse.json({ error: "Too many failed attempts, try again later" }, { status: 429 });
  }
  if (auth !== "ok") {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Body must be JSON" }, { status: 400 });
  }
  const { adapter, target } = (body ?? {}) as { adapter?: unknown; target?: unknown };
  const built = buildJobPayload(adapter, target);
  if (!built.ok) {
    return NextResponse.json({ error: built.error }, { status: 400 });
  }

  try {
    const prisma = await getPrisma();
    const since = new Date(Date.now() - 60_000);
    const [recent, queued] = await Promise.all([
      prisma.job.count({ where: { createdAt: { gte: since } } }),
      prisma.job.count({ where: { status: { in: ["PENDING", "RETRY", "RUNNING"] } } }),
    ]);
    if (recent >= RATE_PER_MINUTE) {
      return NextResponse.json(
        { error: `Rate limit: at most ${RATE_PER_MINUTE} jobs per minute` },
        { status: 429, headers: { "retry-after": "60" } },
      );
    }
    if (queued >= MAX_QUEUED) {
      return NextResponse.json({ error: `Queue is full (${queued} jobs waiting)` }, { status: 429 });
    }

    const job = await prisma.job.create({
      data: {
        type: "run_adapter",
        status: "PENDING",
        payload: built.payload as Prisma.InputJsonValue,
      },
    });
    return NextResponse.json(job, { status: 201 });
  } catch (error) {
    console.error("Error creating job:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
