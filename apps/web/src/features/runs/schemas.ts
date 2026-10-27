import type { FetchOutcome } from "@gov-mine/api-client";
import { z } from "zod";

import { optionalParam, parseSearch, type SearchParams } from "@/lib/lists";

/**
 * Where a paged list of runs is: only the page, since runs come in the API's
 * one order. The first page is the URL without one.
 */
const pageSearchSchema = z.object({
  page: optionalParam(z.coerce.number().int().min(2)),
});

export type PageSearch = z.output<typeof pageSearchSchema>;

export function parsePageSearch(params: SearchParams | URLSearchParams): PageSearch {
  return parseSearch(pageSearchSchema, params);
}

export const runTabs = ["fetches", "snapshots", "documents", "sources", "ai-calls"] as const;
export type RunTab = (typeof runTabs)[number];

export const runTabLabels = {
  fetches: "Fetches",
  snapshots: "Snapshots",
  documents: "Documents",
  sources: "Sources",
  "ai-calls": "AI calls",
} as const satisfies Record<RunTab, string>;

/** Every outcome a fetch can have, in the order the filter shows them. */
export const fetchOutcomes = [
  "fetched",
  "not_modified",
  "unchanged",
  "skipped_scope",
  "skipped_type",
  "skipped_size",
  "skipped_depth",
  "blocked_robots",
  "failed_http",
  "failed_timeout",
] as const satisfies readonly FetchOutcome[];

/**
 * Where the run page is: its tab (the Fetches tab is the URL without one), the
 * tab's page, and on the Fetches tab the outcome and the URL search.
 */
const runSearchSchema = z.object({
  tab: optionalParam(z.enum(["snapshots", "documents", "sources", "ai-calls"])),
  page: optionalParam(z.coerce.number().int().min(2)),
  outcome: optionalParam(z.enum(fetchOutcomes)),
  q: optionalParam(z.string().trim().min(1).max(2048)),
});

export type RunSearch = z.output<typeof runSearchSchema>;

export function parseRunSearch(params: SearchParams | URLSearchParams): RunSearch {
  return parseSearch(runSearchSchema, params);
}
