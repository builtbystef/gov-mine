import { z } from "zod";

import { optionalParam, parseSearch, type SearchParams } from "@/lib/lists";

const textPageSchema = z.object({
  page: optionalParam(z.coerce.number().int().min(1)),
});

/** The page of a snapshot's text the URL asks for, from 1. */
export function parseTextPage(params: SearchParams | URLSearchParams): number {
  return parseSearch(textPageSchema, params).page ?? 1;
}
