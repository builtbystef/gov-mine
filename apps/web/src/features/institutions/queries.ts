import type { ApiClient } from "@gov-mine/api-client";
import { queryOptions } from "@tanstack/react-query";

import { unwrap } from "@/lib/api/errors";
import type { ListPage } from "@/lib/lists";

export const institutionKeys = {
  all: ["institutions"] as const,
  list: (page: ListPage) => [...institutionKeys.all, "list", page] as const,
  detail: (id: string) => [...institutionKeys.all, "detail", id] as const,
};

export function institutionListQuery(api: ApiClient, page: ListPage) {
  return queryOptions({
    queryKey: institutionKeys.list(page),
    queryFn: async () => unwrap(await api.GET("/institutions", { params: { query: page } })),
  });
}

export function institutionQuery(api: ApiClient, id: string) {
  return queryOptions({
    queryKey: institutionKeys.detail(id),
    queryFn: async () =>
      unwrap(
        await api.GET("/institutions/{institution_id}", {
          params: { path: { institution_id: id } },
        }),
      ),
  });
}
