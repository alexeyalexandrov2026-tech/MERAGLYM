import { defineCloudflareConfig } from "@opennextjs/cloudflare";

// Cloudflare Workers build of the web app (the `meraglym` Worker).
// No incremental cache binding: every page is rendered on demand, matching the
// Worker's existing bindings (ASSETS, IMAGES, WORKER_SELF_REFERENCE).
const config = {
  ...defineCloudflareConfig(),
  // The Prisma client is generated code (not committed), so generate it before
  // `next build`. DATABASE_URL is read at runtime from the Worker's settings.
  buildCommand: "npm run prisma:generate && npm run build",
};

export default config;
