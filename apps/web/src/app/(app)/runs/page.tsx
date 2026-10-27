import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import { Suspense } from "react";

import { TableSkeleton } from "@/components/shared/skeletons";
import { RunsTable } from "@/features/runs/components/runs-table";
import { runListQuery } from "@/features/runs/queries";
import { parsePageSearch } from "@/features/runs/schemas";
import { api } from "@/lib/api/server-client";
import { paged, toSearchString, type SearchParams } from "@/lib/lists";
import { getQueryClient } from "@/lib/query-client";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Runs" };

export default function RunsPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  return (
    <Suspense fallback={<TableSkeleton />}>
      <RunsContent searchParams={searchParams} />
    </Suspense>
  );
}

async function RunsContent({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const [search, timeZone] = await Promise.all([searchParams, getTimeZone()]);
  const filters = parsePageSearch(search);
  const queryClient = getQueryClient();
  await queryClient.prefetchQuery(runListQuery(api, paged(filters)));
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <RunsTable key={toSearchString(filters)} initialFilters={filters} timeZone={timeZone} />
    </HydrationBoundary>
  );
}
