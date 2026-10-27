import { dehydrate, HydrationBoundary } from "@tanstack/react-query";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { DetailSkeleton } from "@/components/shared/skeletons";
import { DocumentDetail } from "@/features/documents/components/document-detail";
import { recordListQuery } from "@/features/records/queries";
import { unwrap } from "@/lib/api/errors";
import { api } from "@/lib/api/server-client";
import { listPage } from "@/lib/lists";
import { getQueryClient } from "@/lib/query-client";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Document" };

type Params = Promise<{ id: string }>;

export default function DocumentPage({ params }: { params: Params }) {
  return (
    <Suspense fallback={<DetailSkeleton />}>
      <DocumentContent params={params} />
    </Suspense>
  );
}

async function DocumentContent({ params }: { params: Params }) {
  const [{ id }, timeZone] = await Promise.all([params, getTimeZone()]);
  const result = await api.GET("/documents/{document_id}", {
    params: { path: { document_id: id } },
  });
  if (result.response.status === 404 || result.response.status === 422) notFound();
  const document = unwrap(result);
  const queryClient = getQueryClient();
  await queryClient.prefetchQuery(recordListQuery(api, { document: id, ...listPage(1) }));
  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <DocumentDetail document={document} timeZone={timeZone} />
    </HydrationBoundary>
  );
}
