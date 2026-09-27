import { NextRequest, NextResponse } from "next/server";
import { getPrisma, getDbMode } from "@/lib/prisma";
import type { Node } from "@prisma/client";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const query = searchParams.get("q");

  if (!query || query.trim().length === 0) {
    return NextResponse.json([]);
  }

  try {
    const prisma = await getPrisma();

    if (getDbMode() === "remote") {
      // PostgreSQL native full-text search, ranked by relevance.
      // websearch_to_tsquery allows operators like "quoted text" or -exclude.
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
    }

    // Local SQLite: no tsvector, so use a case-insensitive LIKE over
    // name/description. Rank name matches above description-only matches, then
    // name matches that start with the query above the rest. Split the query
    // into terms and require each term to appear (AND semantics).
    const terms = query
      .trim()
      .split(/\s+/)
      .filter((t) => t.length > 0)
      .slice(0, 10);

    if (terms.length === 0) {
      return NextResponse.json([]);
    }

    const escapeLike = (s: string) =>
      s.replace(/[\\%_]/g, (ch) => `\\${ch}`);

    const whereClause = terms
      .map(
        () =>
          `((name LIKE ? ESCAPE '\\') OR (COALESCE(description, '') LIKE ? ESCAPE '\\'))`,
      )
      .join(" AND ");

    const params: string[] = [];
    for (const term of terms) {
      const like = `%${escapeLike(term)}%`;
      params.push(like, like);
    }

    // Ranking parameters: exact-ish name match for the first term.
    const firstTerm = escapeLike(terms[0]);
    const namePrefix = `${firstTerm}%`;
    const nameContains = `%${firstTerm}%`;

    const sql = `
      SELECT *
      FROM "Node"
      WHERE ${whereClause}
      ORDER BY
        CASE WHEN name LIKE ? ESCAPE '\\' THEN 0 ELSE 1 END,
        CASE WHEN name LIKE ? ESCAPE '\\' THEN 0 ELSE 1 END,
        length(name),
        name ASC
      LIMIT 100;
    `;

    const nodes = await prisma.$queryRawUnsafe<Node[]>(
      sql,
      ...params,
      namePrefix,
      nameContains,
    );

    return NextResponse.json(nodes);
  } catch (error) {
    console.error("Error executing search:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
