import { expect, test } from "vite-plus/test";

import { ApiError, errorMessage, tooManyAttempts } from "./errors";

function result(status: number, body: unknown, headers: Record<string, string> = {}) {
  const response = new Response(null, { status, headers });
  return { error: body, response };
}

test("a detail string becomes the message", () => {
  const error = ApiError.fromResult(result(401, { detail: "Not authenticated" }));
  expect(error.status).toBe(401);
  expect(errorMessage(error)).toBe("Not authenticated");
  expect(error.retryAfter).toBeNull();
});

test("a 500 quotes the request ID from the header", () => {
  const error = ApiError.fromResult(
    result(
      500,
      {
        detail: "Something went wrong. Quote the request ID when reporting it.",
        request_id: "abc123",
      },
      { "x-request-id": "abc123" },
    ),
  );
  expect(error.requestId).toBe("abc123");
  expect(errorMessage(error)).toBe(
    "Something went wrong. Quote the request ID when reporting it. (request abc123)",
  );
});

test("a 4xx keeps the request ID without showing it", () => {
  const error = ApiError.fromResult(
    result(404, { detail: "Contact not found" }, { "x-request-id": "abc123" }),
  );
  expect(error.requestId).toBe("abc123");
  expect(errorMessage(error)).toBe("Contact not found");
});

test("a 429 says how long to wait, from Retry-After", () => {
  const error = ApiError.fromResult(
    result(429, { detail: "Too many attempts. Try again later." }, { "retry-after": "540" }),
  );
  expect(error.retryAfter).toBe(540);
  expect(errorMessage(error)).toBe("Too many attempts. Try again in 9 minutes.");
});

test("a 429 without Retry-After keeps the plain message", () => {
  const error = ApiError.fromResult(result(429, { detail: "Too many attempts. Try again later." }));
  expect(error.retryAfter).toBeNull();
  expect(errorMessage(error)).toBe("Too many attempts. Try again later.");
});

test("the wait is worded in seconds under a minute, minutes rounded up above", () => {
  expect(tooManyAttempts(1)).toBe("Too many attempts. Try again in 1 second.");
  expect(tooManyAttempts(45)).toBe("Too many attempts. Try again in 45 seconds.");
  expect(tooManyAttempts(60)).toBe("Too many attempts. Try again in 1 minute.");
  expect(tooManyAttempts(61)).toBe("Too many attempts. Try again in 2 minutes.");
});

test("a 422 maps each issue to its body field and lists them all", () => {
  const error = ApiError.fromResult(
    result(422, {
      detail: [
        { loc: ["body", "email"], msg: "value is not a valid email address", type: "value_error" },
        { loc: ["body", "email"], msg: "second message is not used", type: "value_error" },
        { loc: ["body", "company", "id"], msg: "Input should be a valid UUID", type: "uuid" },
        { loc: ["query", "limit"], msg: "Input should be less than 501", type: "less_than" },
        { loc: ["body", 0], msg: "Field required", type: "missing" },
      ],
    }),
  );
  expect(error.status).toBe(422);
  expect(error.fields).toEqual({
    email: "value is not a valid email address",
    "company.id": "Input should be a valid UUID",
    "query.limit": "Input should be less than 501",
  });
  expect(errorMessage(error)).toBe(
    "email: value is not a valid email address; email: second message is not used; " +
      "company.id: Input should be a valid UUID; query.limit: Input should be less than 501; " +
      "Field required",
  );
});

test("a body without a detail falls back to the status", () => {
  const error = ApiError.fromResult(result(502, "<html>Bad Gateway</html>"));
  expect(errorMessage(error)).toBe("Request failed with status 502");
  expect(error.fields).toEqual({});
  const empty = ApiError.fromResult(result(422, { detail: [] }));
  expect(errorMessage(empty)).toBe("Validation error");
});

test("a 429 with a malformed Retry-After keeps the plain message", () => {
  const error = ApiError.fromResult(
    result(429, { detail: "Too many attempts." }, { "retry-after": "soon" }),
  );
  expect(error.retryAfter).toBeNull();
  expect(errorMessage(error)).toBe("Too many attempts. Try again later.");
});

test("errors that are not from the API are worded for the user", () => {
  expect(errorMessage(new TypeError("Failed to fetch"))).toBe("The API could not be reached.");
  expect(errorMessage(new Error("boom"))).toBe("boom");
  expect(errorMessage("plain")).toBe("plain");
  expect(errorMessage(undefined)).toBe("undefined");
});

test("unwrap returns the data of a 2xx and throws the ApiError of anything else", async () => {
  const { unwrap } = await import("./errors");
  expect(unwrap({ data: { id: 1 }, response: new Response(null, { status: 200 }) })).toEqual({
    id: 1,
  });
  expect(() => unwrap(result(404, { detail: "Contact not found" }))).toThrowError(
    expect.objectContaining({ name: "ApiError", status: 404, message: "Contact not found" }),
  );
});
