import type { CitationOutput, RecordDetail as Record } from "@gov-mine/api-client";
import { CircleAlertIcon, CircleCheckIcon, ExternalLinkIcon, FileTextIcon } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/shared/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatDateTime } from "@/lib/formatting/dates";

import { fieldLabel, formatValue, recordTypeLabels } from "../schemas";

/** The snapshot page at the cited page, with the excerpt highlighted. */
export function citationHref(citation: CitationOutput): string {
  const search = new URLSearchParams({ page: String(citation.page), highlight: citation.excerpt });
  return `/snapshots/${citation.snapshot_id}?${search.toString()}#excerpt`;
}

/** The source itself; a PDF opens at the cited page. */
function sourceHref(citation: CitationOutput): string {
  return /\.pdf($|\?)/i.test(citation.url) ? `${citation.url}#page=${citation.page}` : citation.url;
}

function VerifiedBadge({ verified }: { verified: boolean }) {
  return verified ? (
    <Badge variant="secondary" className="text-emerald-700 dark:text-emerald-400">
      <CircleCheckIcon />
      Quote verified
    </Badge>
  ) : (
    <Badge variant="destructive">
      <CircleAlertIcon />
      Not found on page
    </Badge>
  );
}

function Citation({ citation }: { citation: CitationOutput }) {
  return (
    <div className="flex flex-col gap-2 rounded-md border-l-2 border-primary/30 bg-muted/40 px-3 py-2">
      <blockquote className="text-sm text-muted-foreground italic">“{citation.excerpt}”</blockquote>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
        <VerifiedBadge verified={citation.verified} />
        <Link
          href={citationHref(citation)}
          className="inline-flex items-center gap-1 font-medium hover:underline"
        >
          <FileTextIcon className="size-3.5" />
          Page {citation.page} of the snapshot
        </Link>
        <a
          href={sourceHref(citation)}
          target="_blank"
          rel="noreferrer"
          className="inline-flex min-w-0 items-center gap-1 text-muted-foreground hover:underline"
        >
          <ExternalLinkIcon className="size-3.5 shrink-0" />
          <span className="truncate">{citation.url}</span>
        </a>
      </div>
    </div>
  );
}

function Value({ value }: { value: unknown }) {
  const text = formatValue(value);
  return text ? (
    <span className="break-words">{text}</span>
  ) : (
    <span className="text-muted-foreground">–</span>
  );
}

/** A record: every field with the citation behind it, and its history as diffs. */
export function RecordDetail({ record, timeZone }: { record: Record; timeZone: string }) {
  const title = formatValue(record.fields[0]?.value) || record.key || "Record";
  const verified = record.fields.filter((f) => f.citation?.verified).length;
  const cited = record.fields.filter((f) => f.citation).length;

  return (
    <>
      <PageHeader
        title={title}
        description={
          <span className="flex flex-wrap items-center gap-x-2">
            <Badge variant="outline">{recordTypeLabels[record.record_type]}</Badge>
            <span>{record.institution_name}</span>
            <span>·</span>
            <a href={record.url} target="_blank" rel="noreferrer" className="hover:underline">
              {record.document_title ?? record.url}
            </a>
            <span>·</span>
            <span>
              {verified} of {cited} citations verified
            </span>
          </span>
        }
      />
      <section className="mb-10 flex flex-col gap-3">
        <h3 className="text-lg font-semibold">Fields</h3>
        <Card>
          <CardContent className="flex flex-col divide-y">
            {record.fields.map((field) => (
              <div
                key={field.field}
                className="grid gap-2 py-3 first:pt-0 last:pb-0 md:grid-cols-[10rem_1fr]"
              >
                <div className="text-sm text-muted-foreground">{fieldLabel(field.field)}</div>
                <div className="flex min-w-0 flex-col gap-2">
                  <div className="font-medium">
                    <Value value={field.value} />
                  </div>
                  {field.citation && <Citation citation={field.citation} />}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
      <section className="flex flex-col gap-3">
        <h3 className="text-lg font-semibold">History</h3>
        <ol className="flex flex-col gap-3">
          {record.history.map((snapshot, index) => (
            <li key={snapshot.id}>
              <Card>
                <CardContent className="flex flex-col gap-3">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                    <span className="font-medium">
                      {formatDateTime(snapshot.extracted_at, timeZone)}
                    </span>
                    {index === 0 && <Badge>Current</Badge>}
                    {index === record.history.length - 1 && (
                      <Badge variant="outline">First extracted</Badge>
                    )}
                    <Link
                      href={`/snapshots/${snapshot.snapshot_id}`}
                      className="text-muted-foreground hover:underline"
                    >
                      Source snapshot
                    </Link>
                  </div>
                  <table className="w-full text-sm">
                    <tbody className="divide-y">
                      {snapshot.changes.map((change) => (
                        <tr key={change.field} className="align-top">
                          <td className="w-40 py-1.5 pr-3 text-muted-foreground">
                            {fieldLabel(change.field)}
                          </td>
                          <td className="py-1.5">
                            {formatValue(change.before) && (
                              <div className="text-destructive line-through decoration-destructive/50">
                                {formatValue(change.before)}
                              </div>
                            )}
                            <div className="text-emerald-700 dark:text-emerald-400">
                              {formatValue(change.after) || (
                                <span className="text-muted-foreground">removed</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}
