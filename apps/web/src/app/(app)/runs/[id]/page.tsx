import { dehydrate, HydrationBoundary, type QueryClient } from "@tanstack/react-query";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { DetailSkeleton } from "@/components/shared/skeletons";
import { RunDetail } from "@/features/runs/components/run-detail";
import {
  isActive,
  runAiCallsQuery,
  runDocumentsQuery,
  runFetchesQuery,
  runQuery,
  runRecordsQuery,
  runReportQuery,
  runSnapshotsQuery,
  runSourcesQuery,
} from "@/features/runs/queries";
import { parseRunSearch, type RunSearch } from "@/features/runs/schemas";
import { unwrap } from "@/lib/api/errors";
import { api } from "@/lib/api/server-client";
import { paged, toSearchString, type SearchParams } from "@/lib/lists";
import { getQueryClient } from "@/lib/query-client";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Run" };

type Params = Promise<{ id: string }>;

export default function RunPage({
  params,
  searchParams,
}: {
  params: Params;
  searchParams: Promise<SearchParams>;
}) {
  return (
    <Suspense fallback={<DetailSkeleton />}>
      <RunContent params={params} searchParams={searchParams} />
    </Suspense>
  );
}

/** Prefetches the tab the URL is on, with the same key the tab's table asks for. */
async function prefetchTab(queryClient: QueryClient, id: string, search: RunSearch, live: boolean) {
  const page = paged({ page: search.page });
  switch (search.tab) {
    case "snapshots":
      return queryClient.prefetchQuery(runSnapshotsQuery(api, id, page, live));
    case "documents":
      return queryClient.prefetchQuery(runDocumentsQuery(api, id, page, live));
    case "records":
      return queryClient.prefetchQuery(runRecordsQuery(api, id, page, live));
    case "sources":
      return queryClient.prefetchQuery(runSourcesQuery(api, id, page, live));
    case "ai-calls":
      return queryClient.prefetchQuery(runAiCallsQuery(api, id, page, live));
    case undefined:
      return queryClient.prefetchQuery(
        runFetchesQuery(
          api,
          id,
          paged({ page: search.page, outcome: search.outcome, q: search.q }),
          live,
        ),
      );
  }
}

async function RunContent({
  params,
  searchParams,
}: {
  params: Params;
  searchParams: Promise<SearchParams>;
}) {
  const [{ id }, rawSearch, timeZone] = await Promise.all([params, searchParams, getTimeZone()]);
  const search = parseRunSearch(rawSearch);
  // A missing run is a not-found page, so it is read here rather than prefetched.
  const result = await api.GET("/runs/{run_id}", { params: { path: { run_id: id } } });
  if (result.response.status === 404 || result.response.status === 422) notFound();
  const run = unwrap(result);
  const live = isActive(run.status);
  const queryClient = getQueryClient();
  queryClient.setQueryData(runQuery(api, id).queryKey, run);
  await Promise.all([
    queryClient.prefetchQuery(runReportQuery(api, id, live)),
    prefetchTab(queryClient, id, search, live),
  ]);
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <RunDetail key={toSearchString(search)} id={id} search={search} timeZone={timeZone} />
    </HydrationBoundary>
  );
}
