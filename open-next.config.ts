import { defineCloudflareConfig } from "@opennextjs/cloudflare";

// Cloudflare Workers build of the web app (the `meraglym` Worker).
// No incremental cache binding: every page is rendered on demand, matching the
// Worker's existing bindings (ASSETS, IMAGES, WORKER_SELF_REFERENCE).
// OpenNext runs `npm run build`, which generates the Prisma client first.
const config = defineCloudflareConfig();

export default config;
