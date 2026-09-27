import { getPrisma } from "@/lib/prisma";
import Dashboard from "@/components/Dashboard";

export const dynamic = 'force-dynamic';

export default async function Home() {
  const prisma = await getPrisma();
  const rootNodes = await prisma.node.findMany({
    where: {
      parentId: null,
    },
    orderBy: {
      name: 'asc'
    }
  });

  return (
    <main>
      <Dashboard initialNodes={rootNodes} />
    </main>
  );
}
