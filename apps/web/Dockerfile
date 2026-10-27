# The Next.js app. Build from the repository root, where the pnpm workspace and
# lockfile live:
#
#   docker build --file apps/web/Dockerfile --tag gov-mine-web .
#
# `API_URL` is read at runtime (see src/lib/api/server-client.ts), so one
# image serves every environment and no secrets enter the build.

# --- Dependencies -------------------------------------------------------------
# The Node version from .node-version. pnpm is the version pinned in
# package.json "packageManager"; Corepack is deprecated, so npm installs it.
FROM node:24.22.1-bookworm-slim AS deps

RUN npm install --global pnpm@12.3.4

WORKDIR /app

# Manifests only, so the install layer survives source changes. The filter
# installs @gov-mine/web and the workspace packages it depends on.
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api-client/package.json packages/api-client/package.json
RUN --mount=type=cache,id=pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile --filter "@gov-mine/web..."

# --- Build --------------------------------------------------------------------
FROM deps AS build

ENV NEXT_TELEMETRY_DISABLED=1

COPY tsconfig tsconfig
COPY packages/api-client packages/api-client
COPY apps/web apps/web

# `output: "standalone"` in next.config.ts writes a self-contained server with
# only the files it traced into .next/standalone.
RUN pnpm --filter @gov-mine/web exec next build

# --- Runtime ------------------------------------------------------------------
FROM node:24.22.1-bookworm-slim AS runtime

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

WORKDIR /app

# The standalone output mirrors the monorepo layout, so server.js lands under
# apps/web. Static assets and public/ are not traced and are copied alongside.
COPY --from=build --chown=node:node /app/apps/web/.next/standalone ./
COPY --from=build --chown=node:node /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=node:node /app/apps/web/public ./apps/web/public

USER node

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:3000/', {redirect: 'manual'}).then(r => process.exit(r.status < 400 ? 0 : 1), () => process.exit(1))"]

CMD ["node", "apps/web/server.js"]
