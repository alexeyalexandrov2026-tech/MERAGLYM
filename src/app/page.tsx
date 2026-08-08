import prisma from "@/lib/prisma";
import Dashboard from "@/components/Dashboard";

export default async function Home() {
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
