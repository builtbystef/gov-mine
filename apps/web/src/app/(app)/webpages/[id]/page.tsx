import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { DetailSkeleton } from "@/components/shared/skeletons";
import { WebpageDetail } from "@/features/webpages/components/webpage-detail";
import { unwrap } from "@/lib/api/errors";
import { api } from "@/lib/api/server-client";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Webpage" };

type Params = Promise<{ id: string }>;

export default function WebpagePage({ params }: { params: Params }) {
  return (
    <Suspense fallback={<DetailSkeleton />}>
      <WebpageContent params={params} />
    </Suspense>
  );
}

async function WebpageContent({ params }: { params: Params }) {
  const [{ id }, timeZone] = await Promise.all([params, getTimeZone()]);
  const result = await api.GET("/webpages/{webpage_id}", { params: { path: { webpage_id: id } } });
  if (result.response.status === 404 || result.response.status === 422) notFound();
  return <WebpageDetail webpage={unwrap(result)} timeZone={timeZone} />;
}
