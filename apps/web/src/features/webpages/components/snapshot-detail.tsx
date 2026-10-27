import type { SnapshotOutput } from "@gov-mine/api-client";
import { ChevronLeftIcon, ChevronRightIcon, DownloadIcon } from "lucide-react";
import Link from "next/link";

import { Detail } from "@/components/shared/detail-list";
import { PageHeader } from "@/components/shared/layout/page-header";
import { Button } from "@/components/ui/button";
import { formatBytes } from "@/lib/formatting/bytes";
import { formatDateTime } from "@/lib/formatting/dates";

/** A snapshot: what was stored, and one page of the text parsed from it. */
export function SnapshotDetail({
  snapshot,
  page,
  text,
  timeZone,
}: {
  snapshot: SnapshotOutput;
  page: number;
  text: string | null;
  timeZone: string;
}) {
  const pageHref = (to: number) =>
    to > 1 ? `/snapshots/${snapshot.id}?page=${to}` : `/snapshots/${snapshot.id}`;
  return (
    <>
      <PageHeader
        title={<span className="break-all">{snapshot.url}</span>}
        description={`Snapshot ${snapshot.id}`}
      >
        <Button
          variant="outline"
          size="sm"
          render={
            <a href={`/api/snapshots/${snapshot.id}/bytes`} target="_blank" rel="noreferrer" />
          }
          nativeButton={false}
        >
          <DownloadIcon />
          Stored bytes
        </Button>
      </PageHeader>
      <dl className="mb-8 grid gap-3 text-sm md:grid-cols-2">
        <Detail label="Webpage">
          <Link href={`/webpages/${snapshot.webpage_id}`} className="break-all hover:underline">
            {snapshot.url}
          </Link>
        </Detail>
        <Detail label="Written">{formatDateTime(snapshot.created_at, timeZone)}</Detail>
        <Detail label="Type">{snapshot.media_type}</Detail>
        <Detail label="Size">{formatBytes(snapshot.size_bytes)}</Detail>
        <Detail label="Text">{snapshot.text_status}</Detail>
        <Detail label="Parser">{snapshot.parser}</Detail>
        <Detail label="Stated date">{formatDateTime(snapshot.stated_date, timeZone)}</Detail>
        <Detail label="Parse error">{snapshot.text_error}</Detail>
        <Detail label="Hash">
          <span className="font-mono text-xs break-all">{snapshot.content_hash}</span>
        </Detail>
      </dl>
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold">Parsed text, page {page}</h3>
          {snapshot.text_status === "ready" && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                render={page > 1 ? <Link href={pageHref(page - 1)} /> : undefined}
                nativeButton={page <= 1}
              >
                <ChevronLeftIcon />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={text === null}
                render={text !== null ? <Link href={pageHref(page + 1)} /> : undefined}
                nativeButton={text === null}
              >
                Next
                <ChevronRightIcon />
              </Button>
            </div>
          )}
        </div>
        {text === null ? (
          <p className="text-sm text-muted-foreground">
            {snapshot.text_status === "ready"
              ? `The snapshot has no page ${page}.`
              : snapshot.text_status === "parsing"
                ? "The snapshot is still being parsed."
                : "The snapshot has no text."}
          </p>
        ) : (
          <pre className="max-h-[70vh] overflow-auto rounded-lg border bg-muted/40 p-4 text-sm whitespace-pre-wrap">
            {text}
          </pre>
        )}
      </section>
    </>
  );
}
