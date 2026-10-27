import type { RecordType } from "@gov-mine/api-client";
import { z } from "zod";

import { optionalParam, parseSearch, type SearchParams } from "@/lib/lists";

export const recordTypes = [
  "project",
  "news_item",
  "meeting",
  "contact",
  "rfp",
  "grant",
  "contract",
] as const satisfies readonly RecordType[];

export const recordTypeLabels: Record<RecordType, string> = {
  project: "Projects",
  news_item: "News",
  meeting: "Meetings",
  contact: "Contacts",
  rfp: "RFPs",
  grant: "Grants",
  contract: "Contracts",
};

/** Where the Records list is: the record type shown, and the page. */
const recordSearchSchema = z.object({
  type: optionalParam(z.enum(recordTypes)),
  page: optionalParam(z.coerce.number().int().min(2)),
});

export type RecordSearch = z.output<typeof recordSearchSchema>;

export function parseRecordSearch(params: SearchParams | URLSearchParams): RecordSearch {
  return parseSearch(recordSearchSchema, params);
}

/** A field name as a column header: `start_date` reads "Start date". */
export function fieldLabel(field: string): string {
  const words = field.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** A field's value as the API sends it, in words; null is the empty string. */
export function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.map(formatValue).join(", ");
  if (typeof value === "number") return value.toLocaleString("en-US");
  if (typeof value === "string" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}
