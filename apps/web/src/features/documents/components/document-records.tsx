"use client";

import type { RecordSummary } from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";

import { DataTable } from "@/components/shared/data-table";
import { recordColumns } from "@/features/records/components/records-table";
import { recordListQuery } from "@/features/records/queries";
import { browserApi } from "@/lib/api/client";
import { listPage } from "@/lib/lists";

/** The records extracted from one document, a page at a time. */
export function DocumentRecords({
  documentId,
  timeZone,
}: {
  documentId: string;
  timeZone: string;
}) {
  const [page, setPage] = useState(1);
  const { data } = useSuspenseQuery(
    recordListQuery(browserApi, { document: documentId, ...listPage(page) }),
  );
  return (
    <DataTable<RecordSummary>
      columns={recordColumns([], timeZone, true)}
      data={data.items}
      total={data.total}
      page={page}
      onPageChange={setPage}
      emptyMessage="No records were extracted from this document."
    />
  );
}
