import { NextRequest, NextResponse } from "next/server";
import prisma from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const parentIdParam = searchParams.get("parentId");

  let parentId: number | null = null;
  if (parentIdParam !== null && parentIdParam !== "null") {
    parentId = parseInt(parentIdParam, 10);
    if (isNaN(parentId)) {
      return NextResponse.json({ error: "Invalid parentId" }, { status: 400 });
    }
  }

  try {
    const nodes = await prisma.node.findMany({
      where: {
        parentId: parentId,
      },
      orderBy: {
        name: "asc", // Deterministic ordering
      },
    });

    return NextResponse.json(nodes);
  } catch (error) {
    console.error("Error fetching nodes:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
