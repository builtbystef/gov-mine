"use client";

import type { RunOutput } from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { createDataTableColumnHelper, DataTable } from "@/components/shared/data-table";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { browserApi } from "@/lib/api/client";
import { formatDateTime } from "@/lib/formatting/dates";
import { paged } from "@/lib/lists";
import { cn } from "@/lib/utils";

import { runListQuery } from "../queries";
import { parsePageSearch, type PageSearch } from "../schemas";
import { RunStatusBadge } from "./status-badges";

const column = createDataTableColumnHelper<RunOutput>();

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
    column.accessor("finished_at", {
      header: "Finished",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {formatDateTime(row.original.finished_at, timeZone)}
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
      emptyMessage="No runs yet. Start one with `gov-mine run create <institution id> --full`."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}
