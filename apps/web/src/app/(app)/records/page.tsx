import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import { Suspense } from "react";

import { TableSkeleton } from "@/components/shared/skeletons";
import { RecordsTable } from "@/features/records/components/records-table";
import { recordListQuery, recordTypesQuery } from "@/features/records/queries";
import { parseRecordSearch } from "@/features/records/schemas";
import { api } from "@/lib/api/server-client";
import { paged, toSearchString, type SearchParams } from "@/lib/lists";
import { getQueryClient } from "@/lib/query-client";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Records" };

export default function RecordsPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  return (
    <Suspense fallback={<TableSkeleton />}>
      <RecordsContent searchParams={searchParams} />
    </Suspense>
  );
}

async function RecordsContent({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const [search, timeZone] = await Promise.all([searchParams, getTimeZone()]);
  const filters = parseRecordSearch(search);
  const queryClient = getQueryClient();
  await Promise.all([
    queryClient.prefetchQuery(recordTypesQuery(api)),
    queryClient.prefetchQuery(recordListQuery(api, paged(filters))),
  ]);
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <RecordsTable key={toSearchString(filters)} initialFilters={filters} timeZone={timeZone} />
    </HydrationBoundary>
  );
}
