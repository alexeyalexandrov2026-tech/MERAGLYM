// Fallback type declarations for the desktop-only SQLite stack.
//
// The SQLite Prisma client (generated into src/generated/prisma-sqlite by
// `npm run prisma:generate`) and `@prisma/adapter-better-sqlite3` (an optional
// dependency whose native build may be skipped outside the desktop build) are
// only used by the Windows desktop build. Web builds (Cloudflare/OpenNext,
// Docker, CI) remove the SQLite branch as dead code and may have neither.
// TypeScript falls back to these ambient declarations only when the real
// modules cannot be resolved; when they are present, their own types are used.

declare module "@/generated/prisma-sqlite" {
  export class PrismaClient {
    constructor(options: { adapter: unknown });
    $disconnect(): Promise<void>;
  }
}

declare module "@prisma/adapter-better-sqlite3" {
  export class PrismaBetterSqlite3 {
    constructor(config: { url: string });
  }
}
