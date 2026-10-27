import type { DocumentDetail as Document } from "@gov-mine/api-client";
import Link from "next/link";

import { Detail } from "@/components/shared/detail-list";
import { PageHeader } from "@/components/shared/layout/page-header";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCalendarDate, formatDateTime } from "@/lib/formatting/dates";

import { documentTypeLabel } from "../schemas";
import { DocumentRecords } from "./document-records";

/** A document: its details, its versions newest first, and the records extracted from it. */
export function DocumentDetail({ document, timeZone }: { document: Document; timeZone: string }) {
  return (
    <>
      <PageHeader
        title={document.title ?? "Untitled document"}
        description={
          <span className="flex flex-wrap items-center gap-x-2">
            <Badge variant="outline">{documentTypeLabel(document.document_type)}</Badge>
            <span>{document.institution_name}</span>
          </span>
        }
      />
      <dl className="mb-8 grid gap-3 text-sm md:grid-cols-2">
        <Detail label="Date">{formatCalendarDate(document.document_date)}</Detail>
        <Detail label="Parent">
          {document.parent && (
            <Link href={`/documents/${document.parent.id}`} className="hover:underline">
              {document.parent.title ?? "Untitled document"}
            </Link>
          )}
        </Detail>
        <Detail label="URL">
          <a
            href={document.url}
            target="_blank"
            rel="noreferrer"
            className="break-all hover:underline"
          >
            {document.url}
          </a>
        </Detail>
        <Detail label="Webpage">
          <Link href={`/webpages/${document.webpage_id}`} className="hover:underline">
            Fetches and snapshots
          </Link>
        </Detail>
      </dl>
      <section className="mb-8 flex flex-col gap-3">
        <h3 className="text-lg font-semibold">Versions</h3>
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Stored</TableHead>
                <TableHead>Snapshot</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Text hash</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {document.versions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="h-16 text-center text-muted-foreground">
                    No snapshots yet.
                  </TableCell>
                </TableRow>
              )}
              {document.versions.map((version, index) => (
                <TableRow key={version.snapshot_id}>
                  <TableCell className="whitespace-nowrap">
                    {formatDateTime(version.created_at, timeZone)}
                    {index === 0 && <Badge className="ml-2">Current</Badge>}
                  </TableCell>
                  <TableCell>
                    <Link
                      href={`/snapshots/${version.snapshot_id}`}
                      className="font-mono text-xs hover:underline"
                      title={version.snapshot_id}
                    >
                      {version.snapshot_id.slice(0, 8)}
                    </Link>
                  </TableCell>
                  <TableCell>{version.media_type}</TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {version.text_hash?.slice(0, 12)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>
      <section className="flex flex-col gap-3">
        <h3 className="text-lg font-semibold">Records</h3>
        <DocumentRecords documentId={document.id} timeZone={timeZone} />
      </section>
    </>
  );
}
