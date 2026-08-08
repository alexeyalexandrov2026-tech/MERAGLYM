import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";
import type { NodeModel as Node } from "@/generated/prisma/models";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get("q");

  if (!query || query.trim().length === 0) {
    return NextResponse.json([]);
  }

  try {
    // We use PostgreSQL native full-text search capabilities via Prisma's $queryRaw.
    // It searches across the 'name' and 'description' fields, ranking by relevance.
    // We use websearch_to_tsquery to allow operators like "quoted text" or -exclude.
    const nodes = await prisma.$queryRaw<Node[]>`
      SELECT *
      FROM "Node"
      WHERE to_tsvector('english', name || ' ' || COALESCE(description, '')) @@ websearch_to_tsquery('english', ${query})
      ORDER BY ts_rank(
        to_tsvector('english', name || ' ' || COALESCE(description, '')),
        websearch_to_tsquery('english', ${query})
      ) DESC
      LIMIT 100;
    `;

    return NextResponse.json(nodes);
  } catch (error) {
    console.error("Error executing search:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
