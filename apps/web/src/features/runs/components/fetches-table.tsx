"use client";

import type { FetchOutput } from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";

import { createDataTableColumnHelper, DataTable } from "@/components/shared/data-table";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { browserApi } from "@/lib/api/client";
import { formatBytes } from "@/lib/formatting/bytes";
import { formatDateTime } from "@/lib/formatting/dates";
import { paged } from "@/lib/lists";
import { cn } from "@/lib/utils";

import { runFetchesQuery } from "../queries";
import { parsePageSearch, type PageSearch } from "../schemas";
import { FetchOutcomeBadge } from "./status-badges";

const column = createDataTableColumnHelper<FetchOutput>();

function fetchColumns(timeZone: string) {
  return column.columns([
    column.accessor("url", {
      header: "URL",
      cell: ({ row }) => <span className="break-all">{row.original.url}</span>,
    }),
    column.accessor("outcome", {
      header: "Outcome",
      cell: ({ row }) => <FetchOutcomeBadge outcome={row.original.outcome} />,
    }),
    column.accessor("http_status", { header: "HTTP" }),
    column.accessor("duration_ms", {
      header: "Duration",
      cell: ({ row }) =>
        row.original.duration_ms === null ? "" : `${row.original.duration_ms} ms`,
    }),
    column.accessor("snapshot", {
      header: "Snapshot",
      cell: ({ row }) => <SnapshotCell snapshot={row.original.snapshot} />,
    }),
    column.accessor("requested_at", {
      header: "Requested",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {formatDateTime(row.original.requested_at, timeZone)}
        </span>
      ),
    }),
  ]);
}

function SnapshotCell({ snapshot }: { snapshot: FetchOutput["snapshot"] }) {
  if (snapshot === null) return <span className="text-muted-foreground">None</span>;
  return (
    <span className="flex flex-col gap-0.5">
      <span className="font-mono text-xs" title={snapshot.id}>
        {snapshot.id}
      </span>
      <span className="text-xs text-muted-foreground">
        {snapshot.media_type}, {formatBytes(snapshot.size_bytes)}
      </span>
    </span>
  );
}

/** The run's fetch log, in the order the requests were made, a page at a time. */
export function FetchesTable({
  runId,
  initialFilters,
  timeZone,
}: {
  runId: string;
  initialFilters: PageSearch;
  timeZone: string;
}) {
  const [page, setPage] = useState(initialFilters.page ?? 1);
  const { deferred, isStale } = useUrlFilters(
    { page: page > 1 ? page : undefined },
    parsePageSearch,
  );
  const { data: fetches } = useSuspenseQuery(runFetchesQuery(browserApi, runId, paged(deferred)));

  return (
    <DataTable<FetchOutput>
      columns={fetchColumns(timeZone)}
      data={fetches.items}
      total={fetches.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="No fetches yet."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}
