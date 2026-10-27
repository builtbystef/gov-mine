import type { NextConfig } from "next";

import path from "node:path";

const nextConfig: NextConfig = {
  // Routes prerender a static shell; uncached reads stream behind <Suspense>.
  cacheComponents: true,
  typedRoutes: true,
  reactCompiler: true,
  // The FastAPI collection routes end in a slash (`/contacts/`). Without this,
  // Next.js would 308 `/api/contacts/` to `/api/contacts` before the proxy
  // route handler in src/app/api/[...path] could forward it.
  skipTrailingSlashRedirect: true,
  // apps/web/Dockerfile copies .next/standalone: a server.js plus only the
  // files it traced. The tracing root is the monorepo root, so workspace
  // packages (@gov-mine/api-client) and hoisted node_modules are included.
  output: "standalone",
  outputFileTracingRoot: path.join(import.meta.dirname, "../.."),
  // Nothing here needs framing, sniffing, or the full URL as a referrer (reset
  // and invite links carry their token in the URL). HSTS is ignored over plain
  // HTTP, so it is harmless in development.
  headers: async () => [
    {
      source: "/(.*)",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "X-Frame-Options", value: "DENY" },
        { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
      ],
    },
  ],
};

export default nextConfig;
