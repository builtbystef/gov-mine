"use client";

import type {
  AiCallOutput,
  DocumentOutput,
  RecordSummary,
  SnapshotOutput,
  SourceOutput,
} from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import Link from "next/link";

import { recordColumns } from "@/features/records/components/records-table";
import { createDataTableColumnHelper, DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";
import { browserApi } from "@/lib/api/client";
import { formatBytes } from "@/lib/formatting/bytes";
import { formatDateTime } from "@/lib/formatting/dates";
import { formatCost } from "@/lib/formatting/numbers";
import { cn } from "@/lib/utils";

import {
  runAiCallsQuery,
  runDocumentsQuery,
  runRecordsQuery,
  runSnapshotsQuery,
  runSourcesQuery,
} from "../queries";
import { useRunTabPage } from "./run-tab-page";

interface TabProps {
  runId: string;
  initialPage: number | undefined;
  timeZone: string;
  live: boolean;
}

/** A type or status value as the API sends it, in words. */
function words(value: string): string {
  const text = value.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function WebpageLink({ id, url }: { id: string; url: string }) {
  return (
    <Link
      href={`/webpages/${id}`}
      className="block min-w-60 break-all whitespace-normal hover:underline"
    >
      {url}
    </Link>
  );
}

const snapshotColumn = createDataTableColumnHelper<SnapshotOutput>();

export function snapshotColumns(timeZone: string) {
  return snapshotColumn.columns([
    snapshotColumn.accessor("id", {
      header: "Snapshot",
      cell: ({ row }) => (
        <Link
          href={`/snapshots/${row.original.id}`}
          className="font-mono text-xs hover:underline"
          title={row.original.id}
        >
          {row.original.id.slice(0, 8)}
        </Link>
      ),
    }),
    snapshotColumn.accessor("url", {
      header: "URL",
      cell: ({ row }) => <WebpageLink id={row.original.webpage_id} url={row.original.url} />,
    }),
    snapshotColumn.accessor("media_type", { header: "Type" }),
    snapshotColumn.accessor("size_bytes", {
      header: "Size",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">{formatBytes(row.original.size_bytes)}</span>
      ),
    }),
    snapshotColumn.accessor("text_status", {
      header: "Text",
      cell: ({ row }) => (
        <Badge
          variant={row.original.text_status === "failed" ? "destructive" : "outline"}
          title={row.original.text_error ?? undefined}
        >
          {words(row.original.text_status)}
        </Badge>
      ),
    }),
    snapshotColumn.accessor("created_at", {
      header: "Written",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {formatDateTime(row.original.created_at, timeZone)}
        </span>
      ),
    }),
  ]);
}

/** The snapshots the run wrote, each linked to its page. */
export function SnapshotsTab({ runId, initialPage, timeZone, live }: TabProps) {
  const { page, setPage, listPage, isStale } = useRunTabPage("snapshots", initialPage);
  const { data } = useSuspenseQuery(runSnapshotsQuery(browserApi, runId, listPage, live));
  return (
    <DataTable<SnapshotOutput>
      columns={snapshotColumns(timeZone)}
      data={data.items}
      total={data.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="The run wrote no snapshots."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}

const documentColumn = createDataTableColumnHelper<DocumentOutput>();

function documentColumns(timeZone: string) {
  return documentColumn.columns([
    documentColumn.accessor("document_type", {
      header: "Type",
      cell: ({ row }) => <Badge variant="secondary">{words(row.original.document_type)}</Badge>,
    }),
    documentColumn.accessor("title", {
      header: "Title",
      cell: ({ row }) => (
        <span className="flex flex-col gap-0.5">
          <Link href={`/documents/${row.original.id}`} className="font-medium hover:underline">
            {row.original.title ?? "Untitled"}
          </Link>
          <WebpageLink id={row.original.webpage_id} url={row.original.url} />
        </span>
      ),
    }),
    documentColumn.accessor("document_date", {
      header: "Date",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {formatDateTime(row.original.document_date, timeZone)}
        </span>
      ),
    }),
  ]);
}

/** The documents the run's classifications found, by type. */
export function DocumentsTab({ runId, initialPage, timeZone, live }: TabProps) {
  const { page, setPage, listPage, isStale } = useRunTabPage("documents", initialPage);
  const { data } = useSuspenseQuery(runDocumentsQuery(browserApi, runId, listPage, live));
  return (
    <DataTable<DocumentOutput>
      columns={documentColumns(timeZone)}
      data={data.items}
      total={data.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="The run found no documents."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}

/** The records the run created or amended, by type, each linked to its page. */
export function RecordsTab({ runId, initialPage, timeZone, live }: TabProps) {
  const { page, setPage, listPage, isStale } = useRunTabPage("records", initialPage);
  const { data } = useSuspenseQuery(runRecordsQuery(browserApi, runId, listPage, live));
  return (
    <DataTable<RecordSummary>
      columns={recordColumns([], timeZone, true)}
      data={data.items}
      total={data.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="The run created or amended no records."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}

const sourceColumn = createDataTableColumnHelper<SourceOutput>();

/** `crawl_interval` arrives as an ISO 8601 duration such as "P7D". */
function days(interval: string): string {
  const match = /^P(\d+)D$/.exec(interval);
  if (!match) return interval;
  return match[1] === "1" ? "Every day" : `Every ${match[1]} days`;
}

function sourceColumns(timeZone: string) {
  return sourceColumn.columns([
    sourceColumn.accessor("document_type", {
      header: "Lists",
      cell: ({ row }) => <Badge variant="secondary">{words(row.original.document_type)}</Badge>,
    }),
    sourceColumn.accessor("url", {
      header: "Listing page",
      cell: ({ row }) => <WebpageLink id={row.original.webpage_id} url={row.original.url} />,
    }),
    sourceColumn.accessor("crawl_interval", {
      header: "Revisit",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">{days(row.original.crawl_interval)}</span>
      ),
    }),
    sourceColumn.accessor("next_crawl_at", {
      header: "Next crawl",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {formatDateTime(row.original.next_crawl_at, timeZone)}
        </span>
      ),
    }),
  ]);
}

/** The listing pages the run found, next crawl first. */
export function SourcesTab({ runId, initialPage, timeZone, live }: TabProps) {
  const { page, setPage, listPage, isStale } = useRunTabPage("sources", initialPage);
  const { data } = useSuspenseQuery(runSourcesQuery(browserApi, runId, listPage, live));
  return (
    <DataTable<SourceOutput>
      columns={sourceColumns(timeZone)}
      data={data.items}
      total={data.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="The run found no sources."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}

const callColumn = createDataTableColumnHelper<AiCallOutput>();

function callColumns(timeZone: string) {
  return callColumn.columns([
    callColumn.accessor("purpose", {
      header: "Purpose",
      cell: ({ row }) => <Badge variant="outline">{words(row.original.purpose)}</Badge>,
    }),
    callColumn.accessor("model", {
      header: "Model",
      cell: ({ row }) => (
        <span className="flex flex-col gap-0.5">
          <span className="font-mono text-xs">{row.original.model}</span>
          <span className="text-xs text-muted-foreground">{row.original.provider}</span>
        </span>
      ),
    }),
    callColumn.accessor("input_tokens", {
      header: "Tokens in / out",
      cell: ({ row }) => (
        <span className="whitespace-nowrap tabular-nums">
          {row.original.input_tokens.toLocaleString("en-US")} /{" "}
          {row.original.output_tokens.toLocaleString("en-US")}
        </span>
      ),
    }),
    callColumn.accessor("reported_cost", {
      header: "Reported by OpenRouter",
      cell: ({ row }) =>
        row.original.reported_cost === null ? (
          <span className="text-muted-foreground">Not reported</span>
        ) : (
          formatCost(row.original.reported_cost)
        ),
    }),
    callColumn.accessor("cost", {
      header: "Estimated",
      cell: ({ row }) => formatCost(row.original.cost),
    }),
    callColumn.accessor("created_at", {
      header: "Called",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {formatDateTime(row.original.created_at, timeZone)}
        </span>
      ),
    }),
  ]);
}

/** The run's paid model calls, by purpose. */
export function AiCallsTab({ runId, initialPage, timeZone, live }: TabProps) {
  const { page, setPage, listPage, isStale } = useRunTabPage("ai-calls", initialPage);
  const { data } = useSuspenseQuery(runAiCallsQuery(browserApi, runId, listPage, live));
  return (
    <DataTable<AiCallOutput>
      columns={callColumns(timeZone)}
      data={data.items}
      total={data.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="The run made no paid calls."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}
