# Web image (PostgreSQL). Next.js 16 requires Node >= 20.9 and Prisma 7
# requires ^20.19 || ^22.12, so use Node 22.
FROM node:22-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# The Electron runtime and the SQLite driver are only needed for the Windows
# desktop build. Skip Electron's ~100 MB binary download here; better-sqlite3 is
# an optionalDependency, so npm tolerates its native build being unavailable.
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1

COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Generate the Prisma client and build the web (Postgres) target.
RUN npx prisma generate
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
# Uncomment the following line in case you want to disable telemetry during runtime.
# ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
# The standalone server binds to $HOSTNAME; Docker sets it to the container id,
# so bind to all interfaces explicitly.
ENV HOSTNAME=0.0.0.0

CMD ["node", "server.js"]
