import { NextRequest } from "next/server";
import { afterEach, expect, test, vi } from "vite-plus/test";

import { GET, POST } from "./route";

const upstream = vi.fn<typeof globalThis.fetch>();

function stubUpstream(response: Response) {
  upstream.mockReset();
  upstream.mockResolvedValue(response);
  vi.stubGlobal("fetch", upstream);
}

function sentRequest(): { url: string; init: RequestInit } {
  const [url, init] = upstream.mock.calls[0]!;
  return { url: url instanceof Request ? url.url : url.toString(), init: init! };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

test("forwards the path and query to the API with only the headers it needs", async () => {
  vi.stubEnv("API_URL", "http://api.test");
  stubUpstream(Response.json({ items: [] }, { headers: { "x-request-id": "r1" } }));
  const response = await GET(
    new NextRequest("http://localhost:3000/api/runs/?q=ada&limit=5", {
      headers: {
        cookie: "session=abc",
        accept: "application/json",
        authorization: "Bearer leaked",
        "x-forwarded-for": "1.1.1.1",
      },
    }),
  );

  const { url, init } = sentRequest();
  expect(url).toBe("http://api.test/runs/?q=ada&limit=5");
  const headers = new Headers(init.headers);
  expect(headers.get("accept")).toBe("application/json");
  expect(headers.has("cookie")).toBe(false);
  expect(headers.has("authorization")).toBe(false);
  expect(headers.has("x-forwarded-for")).toBe(false);
  expect(init.method).toBe("GET");
  expect(init.body).toBeNull();
  expect(init.redirect).toBe("manual");
  expect(response.status).toBe(200);
  expect(response.headers.get("x-request-id")).toBe("r1");
  expect(await response.json()).toEqual({ items: [] });
});

test("a body is forwarded and the API's redirects come back", async () => {
  stubUpstream(
    new Response(null, {
      status: 307,
      headers: [
        ["location", "https://bucket.test/signed"],
        ["set-cookie", "session=new; Path=/; HttpOnly"],
        ["x-powered-by", "uvicorn"],
      ],
    }),
  );
  const response = await POST(
    new NextRequest("http://localhost:3000/api/runs/", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: "a@example.com" }),
    }),
  );

  const { init } = sentRequest();
  expect(init.method).toBe("POST");
  expect(new TextDecoder().decode(init.body as ArrayBuffer)).toBe('{"email":"a@example.com"}');
  expect(response.status).toBe(307);
  expect(response.headers.get("location")).toBe("https://bucket.test/signed");
  expect(response.headers.getSetCookie()).toEqual([]);
  expect(response.headers.has("x-powered-by")).toBe(false);
});

test("an oversized body is refused before it is read", async () => {
  stubUpstream(new Response(null, { status: 204 }));
  const response = await POST(
    new NextRequest("http://localhost:3000/api/runs/", {
      method: "POST",
      headers: { "content-length": String(2 * 1024 * 1024) },
      body: "x",
    }),
  );
  expect(response.status).toBe(413);
  expect(await response.json()).toEqual({ detail: "Request body too large." });
  expect(upstream).not.toHaveBeenCalled();
});
