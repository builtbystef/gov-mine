import type { NextRequest } from "next/server";

import { getApiUrl } from "@/lib/api/server-client";

/**
 * Forwards `/api/*` to the FastAPI service, so the browser never needs the
 * API's address or a CORS setup, and the API can stay on a private network.
 *
 * Only the headers that matter cross the boundary. Hop-by-hop headers and
 * anything the API does not need stay on their side.
 *
 * A body above `MAX_BODY_BYTES` is refused before it is buffered.
 */
const MAX_BODY_BYTES = 1024 * 1024;
const REQUEST_HEADERS = ["accept", "content-type"];
const RESPONSE_HEADERS = [
  "content-type",
  "cache-control",
  "location",
  "retry-after",
  "x-request-id",
];

async function proxy(request: NextRequest): Promise<Response> {
  if (Number(request.headers.get("content-length")) > MAX_BODY_BYTES) {
    return Response.json({ detail: "Request body too large." }, { status: 413 });
  }
  const { pathname, search } = request.nextUrl;
  const target = new URL(pathname.replace(/^\/api/, "") + search, getApiUrl());

  const headers = new Headers();
  for (const name of REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value !== null) headers.set(name, value);
  }

  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const upstream = await fetch(target, {
    method: request.method,
    headers,
    body: hasBody ? await request.arrayBuffer() : null,
    redirect: "manual",
    cache: "no-store",
  });

  const responseHeaders = new Headers();
  for (const name of RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value !== null) responseHeaders.set(name, value);
  }

  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export { proxy as DELETE, proxy as GET, proxy as PATCH, proxy as POST, proxy as PUT };
