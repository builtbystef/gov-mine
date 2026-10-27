"use client";

import type { DocumentOutput, DocumentType } from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { createDataTableColumnHelper, DataTable } from "@/components/shared/data-table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { institutionListQuery } from "@/features/institutions/queries";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { browserApi } from "@/lib/api/client";
import { formatCalendarDate } from "@/lib/formatting/dates";
import { ALL_ROWS, paged } from "@/lib/lists";
import { cn } from "@/lib/utils";

import { documentListQuery } from "../queries";
import {
  documentTypeLabel,
  documentTypes,
  parseDocumentSearch,
  type DocumentSearch,
} from "../schemas";

const column = createDataTableColumnHelper<DocumentOutput>();

function documentColumns() {
  return column.columns([
    column.accessor("title", {
      header: "Title",
      cell: ({ row }) => (
        <span className="flex flex-col gap-0.5">
          <Link href={`/documents/${row.original.id}`} className="font-medium hover:underline">
            {row.original.title ?? "Untitled"}
          </Link>
          <span className="text-xs break-all text-muted-foreground">{row.original.url}</span>
        </span>
      ),
    }),
    column.accessor("document_type", {
      header: "Type",
      cell: ({ row }) => (
        <Badge variant="secondary">{documentTypeLabel(row.original.document_type)}</Badge>
      ),
    }),
    column.accessor("document_date", {
      header: "Date",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">{formatCalendarDate(row.original.document_date)}</span>
      ),
    }),
  ]);
}

/** Documents, newest dated first, filtered by institution, type and earliest date. */
export function DocumentsTable({ initialFilters }: { initialFilters: DocumentSearch }) {
  const [institution, setInstitution] = useState(initialFilters.institution);
  const [type, setType] = useState(initialFilters.type);
  const [since, setSince] = useState(initialFilters.since);
  const [page, setPage] = useState(initialFilters.page ?? 1);
  const { deferred, isStale } = useUrlFilters(
    { institution, type, since, page: page > 1 ? page : undefined },
    parseDocumentSearch,
  );
  const { data: institutions } = useSuspenseQuery(institutionListQuery(browserApi, ALL_ROWS));
  const { data: documents } = useSuspenseQuery(documentListQuery(browserApi, paged(deferred)));

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <NativeSelect
          size="sm"
          aria-label="Institution"
          value={institution ?? ""}
          onChange={(event) => {
            setInstitution(event.target.value || undefined);
            setPage(1);
          }}
        >
          <NativeSelectOption value="">All institutions</NativeSelectOption>
          {institutions.items.map((item) => (
            <NativeSelectOption key={item.id} value={item.id}>
              {item.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <NativeSelect
          size="sm"
          aria-label="Type"
          value={type ?? ""}
          onChange={(event) => {
            setType((event.target.value || undefined) as DocumentType | undefined);
            setPage(1);
          }}
        >
          <NativeSelectOption value="">All types</NativeSelectOption>
          {documentTypes.map((value) => (
            <NativeSelectOption key={value} value={value}>
              {documentTypeLabel(value)}
            </NativeSelectOption>
          ))}
        </NativeSelect>
        <label className="flex items-center gap-2 text-sm text-muted-foreground">
          Dated since
          <Input
            type="date"
            className="h-7 w-40"
            value={since ?? ""}
            onChange={(event) => {
              setSince(event.target.value || undefined);
              setPage(1);
            }}
          />
        </label>
      </div>
      <DataTable<DocumentOutput>
        columns={documentColumns()}
        data={documents.items}
        total={documents.total}
        page={page}
        onPageChange={setPage}
        emptyMessage="No documents match."
        className={cn(isStale && "opacity-60 transition-opacity")}
      />
    </div>
  );
}
