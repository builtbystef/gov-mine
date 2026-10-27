import type { ApiClient, RecordType } from "@gov-mine/api-client";
import { queryOptions } from "@tanstack/react-query";

import { unwrap } from "@/lib/api/errors";
import { queryParams, type ListPage } from "@/lib/lists";

export interface RecordListFilters extends ListPage {
  type?: RecordType | undefined;
  document?: string | undefined;
}

export const recordKeys = {
  all: ["records"] as const,
  types: () => [...recordKeys.all, "types"] as const,
  list: (filters: RecordListFilters) => [...recordKeys.all, "list", filters] as const,
  detail: (id: string) => [...recordKeys.all, "detail", id] as const,
};

export function recordTypesQuery(api: ApiClient) {
  return queryOptions({
    queryKey: recordKeys.types(),
    queryFn: async () => unwrap(await api.GET("/record-types")),
    staleTime: Infinity,
  });
}

export function recordListQuery(api: ApiClient, filters: RecordListFilters) {
  return queryOptions({
    queryKey: recordKeys.list(filters),
    queryFn: async () =>
      unwrap(await api.GET("/records", { params: { query: queryParams(filters) } })),
  });
}

export function recordQuery(api: ApiClient, id: string) {
  return queryOptions({
    queryKey: recordKeys.detail(id),
    queryFn: async () =>
      unwrap(await api.GET("/records/{record_id}", { params: { path: { record_id: id } } })),
  });
}
