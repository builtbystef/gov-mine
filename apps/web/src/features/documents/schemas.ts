import type { DocumentType } from "@gov-mine/api-client";
import { z } from "zod";

import { optionalParam, parseSearch, type SearchParams } from "@/lib/lists";

/** Every document type, in the order the filter shows them. */
export const documentTypes = [
  "projects",
  "project_material",
  "press_releases",
  "meeting_minutes",
  "rfp",
  "grants",
  "purchase_order",
  "budget",
  "annual_report",
  "strategic_plan",
  "procurement_guidelines",
  "staff_directory",
  "youtube",
] as const satisfies readonly DocumentType[];

/** A document type as the API sends it, in words: `press_releases` reads "Press releases". */
export function documentTypeLabel(type: DocumentType): string {
  const text = type.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** Where the Documents list is: its institution, type and earliest date, and the page. */
const documentSearchSchema = z.object({
  institution: optionalParam(z.uuid()),
  type: optionalParam(z.enum(documentTypes)),
  since: optionalParam(z.iso.date()),
  page: optionalParam(z.coerce.number().int().min(2)),
});

export type DocumentSearch = z.output<typeof documentSearchSchema>;

export function parseDocumentSearch(params: SearchParams | URLSearchParams): DocumentSearch {
  return parseSearch(documentSearchSchema, params);
}
