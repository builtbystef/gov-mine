"use client";

import { useSuspenseQuery } from "@tanstack/react-query";

import { Detail } from "@/components/shared/detail-list";
import { PageHeader } from "@/components/shared/layout/page-header";
import { browserApi } from "@/lib/api/client";
import { formatDateTime } from "@/lib/formatting/dates";

import { isActive, runQuery } from "../queries";
import type { PageSearch } from "../schemas";
import { FetchesTable } from "./fetches-table";
import { RunCounts } from "./run-counts";
import { RunStatusBadge } from "./status-badges";

/** A run: what it was asked to do, where it stands, and its fetch log. */
export function RunDetail({
  id,
  fetchFilters,
  timeZone,
}: {
  id: string;
  fetchFilters: PageSearch;
  timeZone: string;
}) {
  const { data: run } = useSuspenseQuery(runQuery(browserApi, id));

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
      <section className="flex flex-col gap-4">
        <h3 className="text-lg font-semibold">Fetches</h3>
        <FetchesTable
          runId={run.id}
          initialFilters={fetchFilters}
          timeZone={timeZone}
          live={isActive(run.status)}
        />
      </section>
    </>
  );
}
