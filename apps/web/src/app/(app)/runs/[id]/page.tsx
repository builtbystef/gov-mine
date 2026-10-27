import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { DetailSkeleton } from "@/components/shared/skeletons";
import { RunDetail } from "@/features/runs/components/run-detail";
import { runFetchesQuery, runQuery } from "@/features/runs/queries";
import { parsePageSearch } from "@/features/runs/schemas";
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

async function RunContent({
  params,
  searchParams,
}: {
  params: Params;
  searchParams: Promise<SearchParams>;
}) {
  const [{ id }, search, timeZone] = await Promise.all([params, searchParams, getTimeZone()]);
  const filters = parsePageSearch(search);
  // A missing run is a not-found page, so it is read here rather than prefetched.
  const result = await api.GET("/runs/{run_id}", { params: { path: { run_id: id } } });
  if (result.response.status === 404 || result.response.status === 422) notFound();
  const queryClient = getQueryClient();
  queryClient.setQueryData(runQuery(api, id).queryKey, unwrap(result));
  await queryClient.prefetchQuery(runFetchesQuery(api, id, paged(filters)));
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <RunDetail key={toSearchString(filters)} id={id} fetchFilters={filters} timeZone={timeZone} />
    </HydrationBoundary>
  );
}
