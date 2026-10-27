import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { DetailSkeleton } from "@/components/shared/skeletons";
import { RecordDetail } from "@/features/records/components/record-detail";
import { unwrap } from "@/lib/api/errors";
import { api } from "@/lib/api/server-client";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Record" };

type Params = Promise<{ id: string }>;

export default function RecordPage({ params }: { params: Params }) {
  return (
    <Suspense fallback={<DetailSkeleton />}>
      <RecordContent params={params} />
    </Suspense>
  );
}

async function RecordContent({ params }: { params: Params }) {
  const [{ id }, timeZone] = await Promise.all([params, getTimeZone()]);
  const result = await api.GET("/records/{record_id}", {
    params: { path: { record_id: id } },
  });
  if (result.response.status === 404 || result.response.status === 422) notFound();
  return <RecordDetail record={unwrap(result)} timeZone={timeZone} />;
}
