import type { ApiClient, RunStatus } from "@gov-mine/api-client";
import { queryOptions } from "@tanstack/react-query";

import { unwrap } from "@/lib/api/errors";
import type { ListPage } from "@/lib/lists";

export const runKeys = {
  all: ["runs"] as const,
  list: (page: ListPage) => [...runKeys.all, "list", page] as const,
  detail: (id: string) => [...runKeys.all, "detail", id] as const,
  fetches: (id: string, page: ListPage) => [...runKeys.detail(id), "fetches", page] as const,
};

/** How often a page with a queued or running run asks again for its counts. */
export const LIVE_INTERVAL_MS = 3000;

export function isActive(status: RunStatus): boolean {
  return status === "queued" || status === "running";
}

export function runListQuery(api: ApiClient, page: ListPage) {
  return queryOptions({
    queryKey: runKeys.list(page),
    queryFn: async () => unwrap(await api.GET("/runs", { params: { query: page } })),
    refetchInterval: (query) =>
      query.state.data?.items.some((run) => isActive(run.status)) ? LIVE_INTERVAL_MS : false,
  });
}

export function runQuery(api: ApiClient, id: string) {
  return queryOptions({
    queryKey: runKeys.detail(id),
    queryFn: async () =>
      unwrap(await api.GET("/runs/{run_id}", { params: { path: { run_id: id } } })),
    refetchInterval: (query) =>
      query.state.data && isActive(query.state.data.status) ? LIVE_INTERVAL_MS : false,
  });
}

/** With `live`, the log is asked for again every few seconds, for a run still going. */
export function runFetchesQuery(api: ApiClient, id: string, page: ListPage, live = false) {
  return queryOptions({
    queryKey: runKeys.fetches(id, page),
    refetchInterval: live ? LIVE_INTERVAL_MS : false,
    queryFn: async () =>
      unwrap(
        await api.GET("/runs/{run_id}/fetches", {
          params: { path: { run_id: id }, query: page },
        }),
      ),
  });
}
