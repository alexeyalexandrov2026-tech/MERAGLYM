import "dotenv/config";
import { Pool } from 'pg'
import { PrismaPg } from '@prisma/adapter-pg'
import { PrismaClient } from '@prisma/client'

const connectionString = `${process.env.DATABASE_URL}`
const pool = new Pool({ connectionString })
const adapter = new PrismaPg(pool)
const prisma = new PrismaClient({ adapter })

async function main() {
  console.log("Delegating arf.json ingestion to Python Intelligence Layer...");
  
  // Insert an ETL job for the Python worker to pick up
  const job = await prisma.job.create({
    data: {
      type: "ingest_arf",
      status: "PENDING",
      payload: { file_path: "../../../arf.json" }
    }
  });
  
  console.log(`Created ETL Job ID: ${job.id}. Ensure Python worker is running to process it.`);
}

main()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
