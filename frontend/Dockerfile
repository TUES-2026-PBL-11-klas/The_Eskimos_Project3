# syntax=docker/dockerfile:1

# ---- deps: install dependencies in isolation ----
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---- build: produce the standalone Next.js output ----
FROM node:22-alpine AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- runner: slim runtime, no dev tooling, no node_modules install ----
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
# Run fully isolated against the in-memory mock data (no API needed).
ENV EVENTHUB_USE_MOCK=true

# Run as a non-root user.
RUN addgroup -g 1001 -S nodejs \
  && adduser -S nextjs -u 1001

# The standalone output bundles only the server + the node_modules it needs.
COPY --from=build /app/public ./public
COPY --from=build --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=build --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
