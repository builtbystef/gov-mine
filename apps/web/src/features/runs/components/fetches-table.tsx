"use client";

import type { FetchOutcome, FetchOutput, OutcomeCount } from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import { SearchIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { createDataTableColumnHelper, DataTable } from "@/components/shared/data-table";
import { Button } from "@/components/ui/button";
import { InputGroup, InputGroupAddon, InputGroupInput } from "@/components/ui/input-group";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { browserApi } from "@/lib/api/client";
import { formatBytes } from "@/lib/formatting/bytes";
import { formatDateTime } from "@/lib/formatting/dates";
import { paged } from "@/lib/lists";
import { cn } from "@/lib/utils";

import { runFetchesQuery } from "../queries";
import { fetchOutcomes, parseRunSearch, type RunSearch } from "../schemas";
import { FetchOutcomeBadge, outcomeLabel } from "./status-badges";

const column = createDataTableColumnHelper<FetchOutput>();

function fetchColumns(timeZone: string) {
  return column.columns([
    column.accessor("url", {
      header: "URL",
      cell: ({ row }) => (
        <Link
          href={`/webpages/${row.original.webpage_id}`}
          className="block min-w-60 break-all whitespace-normal hover:underline"
        >
          {row.original.url}
        </Link>
      ),
    }),
    column.accessor("outcome", {
      header: "Outcome",
      cell: ({ row }) => <FetchOutcomeBadge outcome={row.original.outcome} />,
    }),
    column.accessor("http_status", { header: "HTTP" }),
    column.accessor("reason", {
      header: "Reason",
      cell: ({ row }) =>
        row.original.reason === null ? (
          ""
        ) : (
          <span className="text-muted-foreground">{reasonLabel(row.original.reason)}</span>
        ),
    }),
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

/** A refusal reason as the API sends it ("outside_prefix"), in words. */
function reasonLabel(reason: string): string {
  const text = reason.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function SnapshotCell({ snapshot }: { snapshot: FetchOutput["snapshot"] }) {
  if (snapshot === null) return <span className="text-muted-foreground">–</span>;
  return (
    <Link href={`/snapshots/${snapshot.id}`} className="group flex flex-col gap-0.5">
      <span className="font-mono text-xs group-hover:underline" title={snapshot.id}>
        {snapshot.id.slice(0, 8)}
      </span>
      <span className="text-xs text-muted-foreground">
        {snapshot.media_type}, {formatBytes(snapshot.size_bytes)}
      </span>
    </Link>
  );
}

/** One button per outcome the run has, with how many fetches had it, and one for all. */
function OutcomeFilter({
  counts,
  value,
  onChange,
}: {
  counts: OutcomeCount[];
  value: FetchOutcome | undefined;
  onChange: (outcome: FetchOutcome | undefined) => void;
}) {
  const total = counts.reduce((sum, count) => sum + count.fetches, 0);
  const byOutcome = new Map(counts.map((count) => [count.outcome, count.fetches]));
  const shown = fetchOutcomes.filter((outcome) => byOutcome.has(outcome) || outcome === value);
  const option = (outcome: FetchOutcome | undefined, label: string, count: number) => (
    <Button
      key={outcome ?? "all"}
      size="sm"
      variant={value === outcome ? "default" : "outline"}
      onClick={() => onChange(outcome)}
      aria-pressed={value === outcome}
    >
      {label}
      <span className="tabular-nums opacity-70">{count}</span>
    </Button>
  );
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Outcome">
      {option(undefined, "All", total)}
      {shown.map((outcome) => option(outcome, outcomeLabel(outcome), byOutcome.get(outcome) ?? 0))}
    </div>
  );
}

/**
 * The run's fetch log, in the order the requests were made, a page at a time:
 * every attempt, refusals included, filtered by outcome and URL.
 */
export function FetchesTable({
  runId,
  initialFilters,
  outcomeCounts,
  timeZone,
  live,
}: {
  runId: string;
  initialFilters: RunSearch;
  outcomeCounts: OutcomeCount[];
  timeZone: string;
  live: boolean;
}) {
  const [page, setPage] = useState(initialFilters.page ?? 1);
  const [outcome, setOutcome] = useState(initialFilters.outcome);
  const [search, setSearch] = useState(initialFilters.q ?? "");
  const q = useDebouncedValue(search.trim(), 300);
  const { deferred, isStale } = useUrlFilters(
    { outcome, q: q || undefined, page: page > 1 ? page : undefined },
    parseRunSearch,
  );
  const { data: fetches } = useSuspenseQuery(
    runFetchesQuery(
      browserApi,
      runId,
      paged({ page: deferred.page, outcome: deferred.outcome, q: deferred.q }),
      live,
    ),
  );

  // At least a screen tall, so a search that matches few rows leaves the page
  // long enough to stay where it is instead of the browser clamping it to the top.
  return (
    <div className="flex min-h-svh flex-col gap-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <OutcomeFilter
          counts={outcomeCounts}
          value={outcome}
          onChange={(next) => {
            setOutcome(next);
            setPage(1);
          }}
        />
        <InputGroup className="lg:max-w-xs">
          <InputGroupAddon>
            <SearchIcon />
          </InputGroupAddon>
          <InputGroupInput
            type="search"
            placeholder="Search URLs"
            aria-label="Search URLs"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
        </InputGroup>
      </div>
      <DataTable<FetchOutput>
        columns={fetchColumns(timeZone)}
        data={fetches.items}
        total={fetches.total}
        page={page}
        onPageChange={setPage}
        emptyMessage={outcome || q ? "No fetches match." : "No fetches yet."}
        className={cn(isStale && "opacity-60 transition-opacity")}
      />
    </div>
  );
}
