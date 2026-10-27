import type { ApiClient, FetchOutcome, RunStatus } from "@gov-mine/api-client";
import { queryOptions } from "@tanstack/react-query";

import { unwrap } from "@/lib/api/errors";
import { queryParams, type ListPage } from "@/lib/lists";

export interface FetchFilters extends ListPage {
  outcome?: FetchOutcome | undefined;
  q?: string | undefined;
}

export const runKeys = {
  all: ["runs"] as const,
  list: (page: ListPage) => [...runKeys.all, "list", page] as const,
  detail: (id: string) => [...runKeys.all, "detail", id] as const,
  report: (id: string) => [...runKeys.detail(id), "report"] as const,
  fetches: (id: string, filters: FetchFilters) =>
    [...runKeys.detail(id), "fetches", filters] as const,
  snapshots: (id: string, page: ListPage) => [...runKeys.detail(id), "snapshots", page] as const,
  documents: (id: string, page: ListPage) => [...runKeys.detail(id), "documents", page] as const,
  records: (id: string, page: ListPage) => [...runKeys.detail(id), "records", page] as const,
  sources: (id: string, page: ListPage) => [...runKeys.detail(id), "sources", page] as const,
  aiCalls: (id: string, page: ListPage) => [...runKeys.detail(id), "ai-calls", page] as const,
};

/** How often a page with a queued or running run asks again for its counts. */
export const LIVE_INTERVAL_MS = 3000;

export function isActive(status: RunStatus): boolean {
  return status === "queued" || status === "running";
}

const every = (live: boolean) => (live ? LIVE_INTERVAL_MS : false);

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

export function runReportQuery(api: ApiClient, id: string, live = false) {
  return queryOptions({
    queryKey: runKeys.report(id),
    refetchInterval: every(live),
    queryFn: async () =>
      unwrap(await api.GET("/runs/{run_id}/report", { params: { path: { run_id: id } } })),
  });
}

/** With `live`, the log is asked for again every few seconds, for a run still going. */
export function runFetchesQuery(api: ApiClient, id: string, filters: FetchFilters, live = false) {
  return queryOptions({
    queryKey: runKeys.fetches(id, filters),
    refetchInterval: every(live),
    queryFn: async () =>
      unwrap(
        await api.GET("/runs/{run_id}/fetches", {
          params: { path: { run_id: id }, query: queryParams(filters) },
        }),
      ),
  });
}

export function runSnapshotsQuery(api: ApiClient, id: string, page: ListPage, live = false) {
  return queryOptions({
    queryKey: runKeys.snapshots(id, page),
    refetchInterval: every(live),
    queryFn: async () =>
      unwrap(
        await api.GET("/runs/{run_id}/snapshots", {
          params: { path: { run_id: id }, query: page },
        }),
      ),
  });
}

export function runDocumentsQuery(api: ApiClient, id: string, page: ListPage, live = false) {
  return queryOptions({
    queryKey: runKeys.documents(id, page),
    refetchInterval: every(live),
    queryFn: async () =>
      unwrap(
        await api.GET("/runs/{run_id}/documents", {
          params: { path: { run_id: id }, query: page },
        }),
      ),
  });
}

export function runRecordsQuery(api: ApiClient, id: string, page: ListPage, live = false) {
  return queryOptions({
    queryKey: runKeys.records(id, page),
    refetchInterval: every(live),
    queryFn: async () =>
      unwrap(await api.GET("/records", { params: { query: { run: id, ...page } } })),
  });
}

export function runSourcesQuery(api: ApiClient, id: string, page: ListPage, live = false) {
  return queryOptions({
    queryKey: runKeys.sources(id, page),
    refetchInterval: every(live),
    queryFn: async () =>
      unwrap(
        await api.GET("/runs/{run_id}/sources", {
          params: { path: { run_id: id }, query: page },
        }),
      ),
  });
}

export function runAiCallsQuery(api: ApiClient, id: string, page: ListPage, live = false) {
  return queryOptions({
    queryKey: runKeys.aiCalls(id, page),
    refetchInterval: every(live),
    queryFn: async () =>
      unwrap(await api.GET("/ai-calls", { params: { query: { run: id, ...page } } })),
  });
}
