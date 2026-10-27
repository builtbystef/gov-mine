"use client";

import type { InstitutionOutput } from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { createDataTableColumnHelper, DataTable } from "@/components/shared/data-table";
import { Button } from "@/components/ui/button";
import { StartRunButton } from "@/features/runs/components/start-run-button";
import { RunStatusBadge } from "@/features/runs/components/status-badges";
import { parsePageSearch, type PageSearch } from "@/features/runs/schemas";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { browserApi } from "@/lib/api/client";
import { formatDateTime } from "@/lib/formatting/dates";
import { paged } from "@/lib/lists";
import { cn } from "@/lib/utils";

import { institutionListQuery } from "../queries";
import { institutionTypeLabels } from "../schemas";

const column = createDataTableColumnHelper<InstitutionOutput>();

function institutionColumns(timeZone: string) {
  return column.columns([
    column.accessor("name", {
      header: "Name",
      cell: ({ row }) => (
        <span className="flex flex-col gap-0.5">
          <span className="font-medium">{row.original.name}</span>
          <span className="text-xs text-muted-foreground">
            {[row.original.city, row.original.state, row.original.country_code]
              .filter(Boolean)
              .join(", ")}
          </span>
        </span>
      ),
    }),
    column.accessor("institution_type", {
      header: "Type",
      cell: ({ row }) => institutionTypeLabels[row.original.institution_type],
    }),
    column.accessor("website_url", {
      header: "Website",
      cell: ({ row }) => (
        <a
          href={row.original.website_url}
          target="_blank"
          rel="noreferrer"
          className="break-all hover:underline"
        >
          {row.original.website_url}
        </a>
      ),
    }),
    column.accessor("last_run", {
      header: "Last run",
      cell: ({ row }) => {
        const run = row.original.last_run;
        if (run === null) return <span className="text-muted-foreground">Never</span>;
        return (
          <Link href={`/runs/${run.id}`} className="flex items-center gap-2 hover:underline">
            <RunStatusBadge status={run.status} />
            <span className="whitespace-nowrap">{formatDateTime(run.created_at, timeZone)}</span>
          </Link>
        );
      },
    }),
    column.accessor("next_run_at", {
      header: "Next run",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {row.original.next_run_at === null ? (
            <span className="text-muted-foreground">Not scheduled</span>
          ) : (
            formatDateTime(row.original.next_run_at, timeZone)
          )}
        </span>
      ),
    }),
    column.display({
      id: "actions",
      header: "",
      cell: ({ row }) => (
        <div className="flex justify-end gap-2">
          <StartRunButton institutionId={row.original.id} />
          <Button
            variant="outline"
            size="sm"
            render={<Link href={`/institutions/${row.original.id}/edit`} />}
            nativeButton={false}
          >
            Edit
          </Button>
        </div>
      ),
    }),
  ]);
}

/** Every institution, by name, a page at a time. */
export function InstitutionsTable({
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
  const { data: institutions } = useSuspenseQuery(
    institutionListQuery(browserApi, paged(deferred)),
  );

  return (
    <DataTable<InstitutionOutput>
      columns={institutionColumns(timeZone)}
      data={institutions.items}
      total={institutions.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="No institutions yet. Add one to start crawling."
      className={cn(isStale && "opacity-60 transition-opacity")}
    />
  );
}
