import type { RecordType } from "@gov-mine/api-client";
import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import { Suspense } from "react";

import { TableSkeleton } from "@/components/shared/skeletons";
import { api } from "@/lib/api/server-client";
import { paged, toSearchString, type SearchParams } from "@/lib/lists";
import { getQueryClient } from "@/lib/query-client";
import { getTimeZone } from "@/lib/time-zone/server";

import { recordListQuery, recordTypesQuery } from "../queries";
import { parseRecordSearch } from "../schemas";
import { RecordsTable } from "./records-table";

/** One record type's own page: its records, with that type's columns. */
export function RecordTypeList({
  type,
  searchParams,
}: {
  type: RecordType;
  searchParams: Promise<SearchParams>;
}) {
  return (
    <Suspense fallback={<TableSkeleton />}>
      <RecordTypeContent type={type} searchParams={searchParams} />
    </Suspense>
  );
}

async function RecordTypeContent({
  type,
  searchParams,
}: {
  type: RecordType;
  searchParams: Promise<SearchParams>;
}) {
  const [search, timeZone] = await Promise.all([searchParams, getTimeZone()]);
  const filters = { ...parseRecordSearch(search), type: undefined };
  const queryClient = getQueryClient();
  await Promise.all([
    queryClient.prefetchQuery(recordTypesQuery(api)),
    queryClient.prefetchQuery(recordListQuery(api, paged({ ...filters, type }))),
  ]);
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <RecordsTable
        key={toSearchString(filters)}
        initialFilters={filters}
        timeZone={timeZone}
        fixedType={type}
      />
    </HydrationBoundary>
  );
}
