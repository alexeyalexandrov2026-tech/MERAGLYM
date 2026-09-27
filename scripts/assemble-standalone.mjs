// Next.js standalone output does not include the static assets or the public
// directory; the framework expects them to be copied next to server.js. This
// script performs that copy so the Electron build has a runnable server bundle.
//
// Run after `next build`. See:
// https://nextjs.org/docs/app/api-reference/config/next-config-js/output
import { cpSync, existsSync, mkdirSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const standalone = path.join(root, ".next", "standalone");

if (!existsSync(standalone)) {
  console.error(
    "Missing .next/standalone. Run `next build` (output: 'standalone') first.",
  );
  process.exit(1);
}

mkdirSync(path.join(standalone, ".next"), { recursive: true });

// .next/static -> .next/standalone/.next/static
const staticSrc = path.join(root, ".next", "static");
if (existsSync(staticSrc)) {
  cpSync(staticSrc, path.join(standalone, ".next", "static"), {
    recursive: true,
  });
}

// public -> .next/standalone/public
const publicSrc = path.join(root, "public");
if (existsSync(publicSrc)) {
  cpSync(publicSrc, path.join(standalone, "public"), { recursive: true });
}

console.log("Assembled standalone bundle at .next/standalone");
