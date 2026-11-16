/**
 * Minimal protection for job creation / job results:
 *  - a shared admin token (env/secret JOBS_ADMIN_TOKEN) sent in the
 *    `x-admin-token` header (or `Authorization: Bearer …`);
 *  - a best-effort per-client limit on failed token attempts (per isolate);
 *  - a global DB-backed creation rate limit (see route.ts).
 * If JOBS_ADMIN_TOKEN is not configured, job creation is disabled.
 */

const FAILED_WINDOW_MS = 10 * 60 * 1000;
const MAX_FAILED = 10;
const failed = new Map<string, { count: number; first: number }>();

export function clientKey(request: Request): string {
  return (
    request.headers.get("cf-connecting-ip") ??
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    "local"
  );
}

function timingSafeEqual(a: string, b: string): boolean {
  const enc = new TextEncoder();
  const x = enc.encode(a);
  const y = enc.encode(b);
  let diff = x.length ^ y.length;
  const len = Math.max(x.length, y.length);
  for (let i = 0; i < len; i++) {
    diff |= (x[i] ?? 0) ^ (y[i] ?? 0);
  }
  return diff === 0;
}

export function presentedToken(request: Request): string | null {
  const header = request.headers.get("x-admin-token");
  if (header) return header.trim();
  const auth = request.headers.get("authorization");
  if (auth?.toLowerCase().startsWith("bearer ")) return auth.slice(7).trim();
  return null;
}

export type AuthResult = "ok" | "missing" | "invalid" | "locked" | "disabled";

/**
 * `countFailures: false` is for read-only polling (GET /api/jobs): a wrong or
 * half-typed token there just yields redacted data and must not lock the
 * admin out of POST. Brute force via GET is impractical for a >=16-char random
 * token and only ever reveals what the token already protects.
 */
export function checkAdmin(request: Request, opts: { countFailures?: boolean } = {}): AuthResult {
  const countFailures = opts.countFailures ?? true;
  const expected = process.env.JOBS_ADMIN_TOKEN;
  if (!expected || expected.length < 16) return "disabled";
  const key = clientKey(request);
  const now = Date.now();
  const entry = failed.get(key);
  if (countFailures && entry && now - entry.first < FAILED_WINDOW_MS && entry.count >= MAX_FAILED) {
    return "locked";
  }
  const token = presentedToken(request);
  if (!token) return "missing";
  if (timingSafeEqual(token, expected)) {
    failed.delete(key);
    return "ok";
  }
  if (!countFailures) return "invalid";
  if (!entry || now - entry.first >= FAILED_WINDOW_MS) {
    failed.set(key, { count: 1, first: now });
  } else {
    entry.count += 1;
  }
  if (failed.size > 5000) failed.clear();
  return "invalid";
}
