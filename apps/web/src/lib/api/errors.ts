/** One item of FastAPI's request validation `detail`. */
interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/** The shape openapi-fetch returns from every request. */
interface ApiResult<T> {
  data?: T;
  error?: unknown;
  response: Response;
}

/** A non-2xx response from the API, with FastAPI's `detail` turned into a message. */
export class ApiError extends Error {
  override readonly name = "ApiError";

  constructor(
    readonly status: number,
    message: string,
    /** Per-field messages from a 422, keyed by the body field name. */
    readonly fields: Readonly<Record<string, string>> = {},
    /** Seconds to wait, from a 429's `Retry-After` header. */
    readonly retryAfter: number | null = null,
    /** The API's `X-Request-ID`, which finds the request's log lines. */
    readonly requestId: string | null = null,
  ) {
    super(message);
  }

  static fromResult(result: ApiResult<unknown>): ApiError {
    const { response, error } = result;
    const detail = isRecord(error) ? error["detail"] : undefined;
    const requestId = response.headers.get("x-request-id");
    if (response.status === 429) {
      const retryAfter = retryAfterSeconds(response);
      return new ApiError(response.status, tooManyAttempts(retryAfter), {}, retryAfter, requestId);
    }
    if (response.status >= 500 && requestId) {
      // The API's own 500 says to quote the ID; show it so the user can.
      const message = typeof detail === "string" ? detail : "Something went wrong.";
      return new ApiError(
        response.status,
        `${message} (request ${requestId})`,
        {},
        null,
        requestId,
      );
    }
    if (typeof detail === "string") {
      return new ApiError(response.status, detail, {}, null, requestId);
    }
    if (Array.isArray(detail)) {
      // FastAPI request validation: [{ loc: ["body", "email"], msg, type }].
      const fields: Record<string, string> = {};
      const messages: string[] = [];
      for (const issue of detail as ValidationError[]) {
        const field = issue.loc
          .filter((part): part is string => typeof part === "string" && part !== "body")
          .join(".");
        if (field) fields[field] ??= issue.msg;
        messages.push(field ? `${field}: ${issue.msg}` : issue.msg);
      }
      return new ApiError(
        response.status,
        messages.join("; ") || "Validation error",
        fields,
        null,
        requestId,
      );
    }
    return new ApiError(
      response.status,
      response.statusText || `Request failed with status ${response.status}`,
      {},
      null,
      requestId,
    );
  }
}

export function unwrap<T>(result: ApiResult<T>): T {
  if (result.response.ok) {
    return result.data as T;
  }
  throw ApiError.fromResult(result);
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof TypeError) return "The API could not be reached.";
  if (error instanceof Error) return error.message;
  return String(error);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function retryAfterSeconds(response: Response): number | null {
  const seconds = Number(response.headers.get("retry-after"));
  return Number.isInteger(seconds) && seconds > 0 ? seconds : null;
}

export function tooManyAttempts(seconds: number | null): string {
  if (seconds === null) return "Too many attempts. Try again later.";
  if (seconds < 60)
    return `Too many attempts. Try again in ${seconds} second${seconds === 1 ? "" : "s"}.`;
  const minutes = Math.ceil(seconds / 60);
  return `Too many attempts. Try again in ${minutes} minute${minutes === 1 ? "" : "s"}.`;
}
