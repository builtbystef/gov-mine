import type { ApiClient, DocumentType } from "@gov-mine/api-client";
import { queryOptions } from "@tanstack/react-query";

import { unwrap } from "@/lib/api/errors";
import { queryParams, type ListPage } from "@/lib/lists";

export interface DocumentListFilters extends ListPage {
  institution?: string | undefined;
  type?: DocumentType | undefined;
  since?: string | undefined;
}

export const documentKeys = {
  all: ["documents"] as const,
  list: (filters: DocumentListFilters) => [...documentKeys.all, "list", filters] as const,
};

export function documentListQuery(api: ApiClient, filters: DocumentListFilters) {
  return queryOptions({
    queryKey: documentKeys.list(filters),
    queryFn: async () =>
      unwrap(await api.GET("/documents", { params: { query: queryParams(filters) } })),
  });
}
