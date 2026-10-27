import { createApiClient, type ApiClient } from "@gov-mine/api-client";

/**
 * The typed client for Client Components. It talks to the proxy route handler
 * in `src/app/api/[...path]`, which forwards to the API.
 */
export const browserApi: ApiClient = createApiClient({ baseUrl: "/api" });
