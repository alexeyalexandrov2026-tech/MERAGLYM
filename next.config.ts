import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // The SQLite driver, its native addon, and the generated SQLite Prisma client
  // are loaded via dynamic import (see src/lib/prisma.ts), so Next's tracer does
  // not pick them up automatically. Force them into the standalone bundle used
  // by the desktop build.
  outputFileTracingIncludes: {
    "/": [
      "./node_modules/better-sqlite3/**",
      "./node_modules/node-addon-api/**",
      "./node_modules/@prisma/adapter-better-sqlite3/**",
      "./src/generated/prisma-sqlite/**",
    ],
    "/api/**": [
      "./node_modules/better-sqlite3/**",
      "./node_modules/node-addon-api/**",
      "./node_modules/@prisma/adapter-better-sqlite3/**",
      "./src/generated/prisma-sqlite/**",
    ],
  },
  // Keep the native module external so it is required at runtime rather than
  // bundled by the server compiler.
  serverExternalPackages: [
    "better-sqlite3",
    "@prisma/adapter-better-sqlite3",
    "@prisma/adapter-pg",
    "pg",
  ],
};

export default nextConfig;
