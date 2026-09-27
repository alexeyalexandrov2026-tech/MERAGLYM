import type { NextConfig } from "next";

// The desktop (Electron) build sets MERAGLYM_TARGET=desktop at build time. Every
// other build — the Cloudflare/OpenNext web deploy, Docker, CI — is a "web"
// build and stays exactly as before: PostgreSQL only, with no SQLite code or
// native modules in the bundle.
const isDesktop = process.env.MERAGLYM_TARGET === "desktop";

// Files the embedded-SQLite path needs at runtime. They are loaded via dynamic
// import (see src/lib/prisma.ts), so Next's tracer does not pick them up
// automatically; force them into the standalone bundle for the desktop build.
const sqliteRuntimeFiles = [
  "./node_modules/better-sqlite3/**",
  "./node_modules/node-addon-api/**",
  "./node_modules/@prisma/adapter-better-sqlite3/**",
  "./src/generated/prisma-sqlite/**",
];

const nextConfig: NextConfig = {
  output: "standalone",
  // Inlined at build time, so `process.env.MERAGLYM_TARGET === "desktop"` is a
  // constant and the SQLite branch is removed from web builds entirely.
  env: {
    MERAGLYM_TARGET: isDesktop ? "desktop" : "web",
  },
  ...(isDesktop
    ? {
        outputFileTracingIncludes: {
          "/": sqliteRuntimeFiles,
          "/api/**": sqliteRuntimeFiles,
        },
        // Keep the native driver external so it is required at runtime rather
        // than bundled by the server compiler.
        serverExternalPackages: ["better-sqlite3", "@prisma/adapter-better-sqlite3"],
      }
    : {}),
};

export default nextConfig;
