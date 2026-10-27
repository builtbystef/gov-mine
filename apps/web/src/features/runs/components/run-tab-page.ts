import { useState } from "react";

import { useUrlFilters } from "@/hooks/use-url-filters";
import { paged, type ListPage } from "@/lib/lists";

import { parseRunSearch, type RunTab } from "../schemas";

/** A run tab's page, kept in the URL next to the tab it belongs to. */
export function useRunTabPage(
  tab: Exclude<RunTab, "fetches">,
  initialPage: number | undefined,
): { page: number; setPage: (page: number) => void; listPage: ListPage; isStale: boolean } {
  const [page, setPage] = useState(initialPage ?? 1);
  const { deferred, isStale } = useUrlFilters(
    { tab, page: page > 1 ? page : undefined },
    parseRunSearch,
  );
  return { page, setPage, listPage: paged({ page: deferred.page }), isStale };
}
