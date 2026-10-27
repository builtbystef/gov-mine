import { z } from "zod";

import { optionalParam, parseSearch, type SearchParams } from "@/lib/lists";

/**
 * Where a paged list of runs or of a run's fetches is: only the page, since
 * both come in the API's one order. The first page is the URL without one.
 */
const pageSearchSchema = z.object({
  page: optionalParam(z.coerce.number().int().min(2)),
});

export type PageSearch = z.output<typeof pageSearchSchema>;

export function parsePageSearch(params: SearchParams | URLSearchParams): PageSearch {
  return parseSearch(pageSearchSchema, params);
}
