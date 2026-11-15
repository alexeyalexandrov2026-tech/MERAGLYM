import { NextRequest, NextResponse } from "next/server";
import type { Prisma } from "@prisma/client";
import { getPrisma, getDbMode } from "@/lib/prisma";
import { rankNodes, toSearchTerms } from "@/lib/search";

// Upper bound on candidate rows fetched before ranking (the whole OSINT tree is
// ~1.4k nodes, so this only guards against pathological queries).
const MAX_CANDIDATES = 2000;

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q") ?? "";
  const terms = toSearchTerms(query);

  if (terms.length === 0) {
    return NextResponse.json([]);
  }

  try {
    const prisma = await getPrisma();

    // Case-insensitive substring match on every term. PostgreSQL needs
    // `mode: "insensitive"`; SQLite's LIKE is already case-insensitive and its
    // Prisma client does not accept `mode`.
    const insensitive: { mode?: Prisma.QueryMode } =
      getDbMode() === "remote" ? { mode: "insensitive" } : {};
    const candidates = await prisma.node.findMany({
      where: {
        OR: terms.flatMap((term) => [
          { name: { contains: term, ...insensitive } },
          { description: { contains: term, ...insensitive } },
        ]),
      },
      take: MAX_CANDIDATES,
    });

    return NextResponse.json(rankNodes(candidates, query, terms));
  } catch (error) {
    console.error("Error executing search:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
