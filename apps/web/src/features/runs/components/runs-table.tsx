"use client";

import type { RunOutput } from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { createDataTableColumnHelper, DataTable } from "@/components/shared/data-table";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { browserApi } from "@/lib/api/client";
import { formatDateTime } from "@/lib/formatting/dates";
import { formatCost, formatDuration } from "@/lib/formatting/numbers";
import { paged } from "@/lib/lists";
import { cn } from "@/lib/utils";

import { runListQuery } from "../queries";
import { parsePageSearch, type PageSearch } from "../schemas";
import { RunStatusBadge } from "./status-badges";

const column = createDataTableColumnHelper<RunOutput>();

type CountKey = Exclude<keyof RunOutput["counts"], "cost">;

function countColumn(key: CountKey, header: string) {
  return column.display({
    id: key,
    header: () => <span className="block text-right">{header}</span>,
    cell: ({ row }) => {
      const value = row.original.counts[key];
      return (
        <span
          className={cn(
            "block text-right tabular-nums",
            value === 0 && "text-muted-foreground",
            key === "failed" && value > 0 && "font-medium text-destructive",
          )}
        >
          {value}
        </span>
      );
    },
  });
}

function runColumns(timeZone: string) {
  return column.columns([
    column.accessor("institution_name", {
      header: "Institution",
      cell: ({ row }) => (
        <Link href={`/runs/${row.original.id}`} className="font-medium hover:underline">
          {row.original.institution_name}
        </Link>
      ),
    }),
    column.accessor("status", {
      header: "Status",
      cell: ({ row }) => <RunStatusBadge status={row.original.status} />,
    }),
    column.display({
      id: "trigger",
      header: "Trigger",
      cell: ({ row }) => `${row.original.settings.trigger}, ${row.original.settings.mode}`,
    }),
    column.accessor("created_at", {
      header: "Created",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {formatDateTime(row.original.created_at, timeZone)}
        </span>
      ),
    }),
    column.accessor("elapsed_seconds", {
      header: "Elapsed",
      cell: ({ row }) => (
        <span className="whitespace-nowrap tabular-nums">
          {formatDuration(row.original.elapsed_seconds)}
        </span>
      ),
    }),
    countColumn("fetched", "Fetched"),
    countColumn("not_modified", "Not modified"),
    countColumn("skipped", "Skipped"),
    countColumn("blocked", "Blocked"),
    countColumn("failed", "Failed"),
    countColumn("snapshots", "Snapshots"),
    column.display({
      id: "cost",
      header: () => <span className="block text-right">Cost</span>,
      cell: ({ row }) => (
        <span className="block text-right tabular-nums">
          {formatCost(row.original.counts.cost)}
        </span>
      ),
    }),
  ]);
}

/** Every run, newest first, a page at a time. */
export function RunsTable({
  initialFilters,
  timeZone,
}: {
  initialFilters: PageSearch;
  timeZone: string;
}) {
  const [page, setPage] = useState(initialFilters.page ?? 1);
  const { deferred, isStale } = useUrlFilters(
    { page: page > 1 ? page : undefined },
    parsePageSearch,
  );
  const { data: runs } = useSuspenseQuery(runListQuery(browserApi, paged(deferred)));

  return (
    <DataTable<RunOutput>
      columns={runColumns(timeZone)}
      data={runs.items}
      total={runs.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="No runs yet. Start one from Institutions."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}
