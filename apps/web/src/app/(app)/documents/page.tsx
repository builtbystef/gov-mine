import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import { Suspense } from "react";

import { TableSkeleton } from "@/components/shared/skeletons";
import { DocumentsTable } from "@/features/documents/components/documents-table";
import { documentListQuery } from "@/features/documents/queries";
import { parseDocumentSearch } from "@/features/documents/schemas";
import { institutionListQuery } from "@/features/institutions/queries";
import { api } from "@/lib/api/server-client";
import { ALL_ROWS, paged, toSearchString, type SearchParams } from "@/lib/lists";
import { getQueryClient } from "@/lib/query-client";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Documents" };

export default function DocumentsPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  return (
    <Suspense fallback={<TableSkeleton />}>
      <DocumentsContent searchParams={searchParams} />
    </Suspense>
  );
}

async function DocumentsContent({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const [search, timeZone] = await Promise.all([searchParams, getTimeZone()]);
  const filters = parseDocumentSearch(search);
  const queryClient = getQueryClient();
  await Promise.all([
    queryClient.prefetchQuery(institutionListQuery(api, ALL_ROWS)),
    queryClient.prefetchQuery(documentListQuery(api, paged(filters))),
  ]);
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <DocumentsTable key={toSearchString(filters)} initialFilters={filters} timeZone={timeZone} />
    </HydrationBoundary>
  );
}
