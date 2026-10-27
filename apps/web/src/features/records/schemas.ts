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

/** Each record type's own page under /records, by its URL segment. */
export const recordTypeSlugs = {
  project: "projects",
  news_item: "news-items",
  meeting: "meetings",
  contact: "contacts",
  rfp: "rfps",
  grant: "grants",
  contract: "contracts",
} as const satisfies Record<RecordType, string>;

/** The fields a type's own page shows as columns, most telling first. */
export const recordTypeColumns: Record<RecordType, string[]> = {
  project: ["name", "phase", "location", "start_date", "end_date"],
  news_item: ["headline", "published_at", "summary"],
  meeting: ["held_at", "body", "video_url"],
  contact: ["name", "title", "email", "phone"],
  rfp: ["title", "status", "due_date", "published_at", "solicitation_number"],
  grant: ["title", "awardee_name", "funding_agency", "obligated_amount", "performance_end"],
  contract: ["vendor_name", "total_value", "awarded_at", "start_date", "end_date"],
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
