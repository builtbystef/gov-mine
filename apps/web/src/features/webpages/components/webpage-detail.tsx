import type { WebpageOutput } from "@gov-mine/api-client";
import Link from "next/link";

import { Detail } from "@/components/shared/detail-list";
import { PageHeader } from "@/components/shared/layout/page-header";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { FetchOutcomeBadge } from "@/features/runs/components/status-badges";
import { formatBytes } from "@/lib/formatting/bytes";
import { formatDateTime } from "@/lib/formatting/dates";

function Empty({ columns, children }: { columns: number; children: string }) {
  return (
    <TableRow>
      <TableCell colSpan={columns} className="h-16 text-center text-muted-foreground">
        {children}
      </TableCell>
    </TableRow>
  );
}

/** A webpage: every fetch of it, newest first, and every snapshot stored from it. */
export function WebpageDetail({ webpage, timeZone }: { webpage: WebpageOutput; timeZone: string }) {
  return (
    <>
      <PageHeader
        title={<span className="break-all">{webpage.url}</span>}
        description={`Webpage ${webpage.id}`}
      />
      <dl className="mb-8 grid gap-3 text-sm md:grid-cols-2">
        <Detail label="Domain">{webpage.domain}</Detail>
        <Detail label="Missing since">{formatDateTime(webpage.missing_since, timeZone)}</Detail>
        <Detail label="URL">
          <a
            href={webpage.url}
            target="_blank"
            rel="noreferrer"
            className="break-all hover:underline"
          >
            {webpage.url}
          </a>
        </Detail>
      </dl>
      <section className="mb-8 flex flex-col gap-3">
        <h3 className="text-lg font-semibold">Fetches</h3>
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Requested</TableHead>
                <TableHead>Run</TableHead>
                <TableHead>Outcome</TableHead>
                <TableHead>HTTP</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Snapshot</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {webpage.fetches.length === 0 && <Empty columns={6}>Never fetched.</Empty>}
              {webpage.fetches.map((fetch) => (
                <TableRow key={fetch.id}>
                  <TableCell className="whitespace-nowrap">
                    {formatDateTime(fetch.requested_at, timeZone)}
                  </TableCell>
                  <TableCell>
                    <Link
                      href={`/runs/${fetch.crawl_run_id}`}
                      className="font-mono text-xs hover:underline"
                      title={fetch.crawl_run_id}
                    >
                      {fetch.crawl_run_id.slice(0, 8)}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <FetchOutcomeBadge outcome={fetch.outcome} />
                  </TableCell>
                  <TableCell>{fetch.http_status}</TableCell>
                  <TableCell className="whitespace-normal text-muted-foreground">
                    {fetch.reason}
                  </TableCell>
                  <TableCell>
                    {fetch.snapshot === null ? (
                      <span className="text-muted-foreground">None</span>
                    ) : (
                      <Link
                        href={`/snapshots/${fetch.snapshot.id}`}
                        className="font-mono text-xs hover:underline"
                      >
                        {fetch.snapshot.id.slice(0, 8)}
                      </Link>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>
      <section className="flex flex-col gap-3">
        <h3 className="text-lg font-semibold">Snapshots</h3>
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Written</TableHead>
                <TableHead>Snapshot</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Text</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {webpage.snapshots.length === 0 && <Empty columns={5}>No snapshots.</Empty>}
              {webpage.snapshots.map((snapshot) => (
                <TableRow key={snapshot.id}>
                  <TableCell className="whitespace-nowrap">
                    {formatDateTime(snapshot.created_at, timeZone)}
                  </TableCell>
                  <TableCell>
                    <Link
                      href={`/snapshots/${snapshot.id}`}
                      className="font-mono text-xs hover:underline"
                      title={snapshot.id}
                    >
                      {snapshot.id.slice(0, 8)}
                    </Link>
                  </TableCell>
                  <TableCell>{snapshot.media_type}</TableCell>
                  <TableCell>{formatBytes(snapshot.size_bytes)}</TableCell>
                  <TableCell>{snapshot.text_status}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>
    </>
  );
}
