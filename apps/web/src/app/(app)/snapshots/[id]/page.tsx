import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { DetailSkeleton } from "@/components/shared/skeletons";
import { SnapshotDetail } from "@/features/webpages/components/snapshot-detail";
import { parseTextPage } from "@/features/webpages/schemas";
import { unwrap } from "@/lib/api/errors";
import { api } from "@/lib/api/server-client";
import type { SearchParams } from "@/lib/lists";
import { getTimeZone } from "@/lib/time-zone/server";

export const metadata: Metadata = { title: "Snapshot" };

type Params = Promise<{ id: string }>;

export default function SnapshotPage({
  params,
  searchParams,
}: {
  params: Params;
  searchParams: Promise<SearchParams>;
}) {
  return (
    <Suspense fallback={<DetailSkeleton />}>
      <SnapshotContent params={params} searchParams={searchParams} />
    </Suspense>
  );
}

async function SnapshotContent({
  params,
  searchParams,
}: {
  params: Params;
  searchParams: Promise<SearchParams>;
}) {
  const [{ id }, search, timeZone] = await Promise.all([params, searchParams, getTimeZone()]);
  const page = parseTextPage(search);
  // A record's citation links here with the excerpt to mark on the page.
  const highlight =
    typeof search.highlight === "string" && search.highlight ? search.highlight : undefined;
  const result = await api.GET("/snapshots/{snapshot_id}", {
    params: { path: { snapshot_id: id } },
  });
  if (result.response.status === 404 || result.response.status === 422) notFound();
  const snapshot = unwrap(result);
  // The text is only asked for once parsing is done; 404 past the last page is shown, not thrown.
  const text =
    snapshot.text_status === "ready"
      ? await api.GET("/snapshots/{snapshot_id}/text/{page}", {
          params: { path: { snapshot_id: id, page } },
          parseAs: "text",
        })
      : null;
  return (
    <SnapshotDetail
      snapshot={snapshot}
      page={page}
      text={text?.response.ok ? (text.data as string) : null}
      timeZone={timeZone}
      highlight={highlight}
    />
  );
}
