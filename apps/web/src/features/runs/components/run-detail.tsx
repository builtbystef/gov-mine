"use client";

import { useSuspenseQuery } from "@tanstack/react-query";
import Link from "next/link";

import { Detail } from "@/components/shared/detail-list";
import { PageHeader } from "@/components/shared/layout/page-header";
import { browserApi } from "@/lib/api/client";
import { formatDateTime } from "@/lib/formatting/dates";
import { toSearchString } from "@/lib/lists";
import { cn } from "@/lib/utils";

import { isActive, runQuery, runReportQuery } from "../queries";
import { runTabLabels, runTabs, type RunSearch } from "../schemas";
import { FetchesTable } from "./fetches-table";
import { RunCounts } from "./run-counts";
import { RunReport } from "./run-report";
import { AiCallsTab, DocumentsTab, RecordsTab, SnapshotsTab, SourcesTab } from "./run-tab-tables";
import { RunStatusBadge } from "./status-badges";

/** A run: what it was asked to do, its numbers, and what it did, a tab per kind. */
export function RunDetail({
  id,
  search,
  timeZone,
}: {
  id: string;
  search: RunSearch;
  timeZone: string;
}) {
  const { data: run } = useSuspenseQuery(runQuery(browserApi, id));
  const live = isActive(run.status);
  const { data: report } = useSuspenseQuery(runReportQuery(browserApi, id, live));
  const tab = search.tab ?? "fetches";
  const tabProps = { runId: run.id, initialPage: search.page, timeZone, live };

  return (
    <>
      <PageHeader
        title={
          <span className="flex flex-wrap items-center gap-3">
            {run.institution_name}
            <RunStatusBadge status={run.status} />
          </span>
        }
        description={`Run ${run.id}`}
      />
      <div className="mb-3">
        <RunReport report={report} />
      </div>
      <div className="mb-6">
        <RunCounts run={run} />
      </div>
      <dl className="mb-8 grid gap-3 text-sm md:grid-cols-2">
        <Detail label="Trigger">{run.settings.trigger}</Detail>
        <Detail label="Mode">{run.settings.mode}</Detail>
        <Detail label="Created">{formatDateTime(run.created_at, timeZone)}</Detail>
        <Detail label="Started">{formatDateTime(run.started_at, timeZone)}</Detail>
        <Detail label="Finished">{formatDateTime(run.finished_at, timeZone)}</Detail>
        <Detail label="Error">{run.error}</Detail>
      </dl>
      <nav className="mb-4 flex gap-1 overflow-x-auto overflow-y-hidden border-b" aria-label="Run">
        {runTabs.map((name) => {
          const query = toSearchString({ tab: name === "fetches" ? undefined : name });
          return (
            <Link
              key={name}
              href={query ? `/runs/${run.id}?${query}` : `/runs/${run.id}`}
              aria-current={name === tab ? "page" : undefined}
              className={cn(
                "-mb-px border-b-2 px-3 py-2 text-sm font-medium whitespace-nowrap transition-colors",
                name === tab
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              {runTabLabels[name]}
            </Link>
          );
        })}
      </nav>
      {tab === "fetches" && (
        <FetchesTable
          runId={run.id}
          initialFilters={search}
          outcomeCounts={report.fetches_by_outcome}
          timeZone={timeZone}
          live={live}
        />
      )}
      {tab === "snapshots" && <SnapshotsTab {...tabProps} />}
      {tab === "documents" && <DocumentsTab {...tabProps} />}
      {tab === "records" && <RecordsTab {...tabProps} />}
      {tab === "sources" && <SourcesTab {...tabProps} />}
      {tab === "ai-calls" && <AiCallsTab {...tabProps} />}
    </>
  );
}
