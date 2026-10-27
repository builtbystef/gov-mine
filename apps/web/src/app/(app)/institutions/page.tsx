import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import { PlusIcon } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { PageHeader } from "@/components/shared/layout/page-header";
import { TableSkeleton } from "@/components/shared/skeletons";
import { Button } from "@/components/ui/button";
import { InstitutionsTable } from "@/features/institutions/components/institutions-table";
import { institutionListQuery } from "@/features/institutions/queries";
import { parsePageSearch } from "@/features/runs/schemas";
import { api } from "@/lib/api/server-client";
import { paged, toSearchString, type SearchParams } from "@/lib/lists";
import { getQueryClient } from "@/lib/query-client";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Institutions" };

export default function InstitutionsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  return (
    <>
      <PageHeader>
        <Button render={<Link href="/institutions/new" />} nativeButton={false}>
          <PlusIcon />
          Add institution
        </Button>
      </PageHeader>
      <Suspense fallback={<TableSkeleton />}>
        <InstitutionsContent searchParams={searchParams} />
      </Suspense>
    </>
  );
}

async function InstitutionsContent({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const [search, timeZone] = await Promise.all([searchParams, getTimeZone()]);
  const filters = parsePageSearch(search);
  const queryClient = getQueryClient();
  await queryClient.prefetchQuery(institutionListQuery(api, paged(filters)));
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <InstitutionsTable
        key={toSearchString(filters)}
        initialFilters={filters}
        timeZone={timeZone}
      />
    </HydrationBoundary>
  );
}
