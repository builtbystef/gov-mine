"use client";

import type { RecordSummary, RecordType } from "@gov-mine/api-client";
import { useSuspenseQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { createDataTableColumnHelper, DataTable } from "@/components/shared/data-table";
import { Button } from "@/components/ui/button";
import { useUrlFilters } from "@/hooks/use-url-filters";
import { browserApi } from "@/lib/api/client";
import { formatDateTime } from "@/lib/formatting/dates";
import { paged } from "@/lib/lists";
import { cn } from "@/lib/utils";

import { recordListQuery, recordTypesQuery } from "../queries";
import {
  fieldLabel,
  formatValue,
  parseRecordSearch,
  recordTypeColumns,
  recordTypeLabels,
  recordTypes,
  type RecordSearch,
} from "../schemas";

const column = createDataTableColumnHelper<RecordSummary>();

function FieldValue({ value }: { value: unknown }) {
  const text = formatValue(value);
  if (!text) return <span className="text-muted-foreground">–</span>;
  return (
    <span className="line-clamp-2 block max-w-72 min-w-24 whitespace-normal" title={text}>
      {text}
    </span>
  );
}

export function recordColumns(fields: string[], timeZone: string, showType: boolean) {
  const [first, ...rest] = fields;
  return column.columns([
    column.display({
      id: "record",
      header: first ? fieldLabel(first) : "Record",
      cell: ({ row }) => (
        <Link href={`/records/${row.original.id}`} className="font-medium hover:underline">
          {formatValue(first ? row.original.data[first] : Object.values(row.original.data)[0]) ||
            row.original.key ||
            "Record"}
        </Link>
      ),
    }),
    ...(showType
      ? [
          column.accessor("record_type", {
            header: "Type",
            cell: ({ row }) => recordTypeLabels[row.original.record_type],
          }),
        ]
      : []),
    ...rest.map((field) =>
      column.display({
        id: field,
        header: fieldLabel(field),
        cell: ({ row }) => <FieldValue value={row.original.data[field]} />,
      }),
    ),
    column.accessor("document_title", {
      header: "Document",
      cell: ({ row }) => (
        <a href={row.original.url} target="_blank" rel="noreferrer" className="hover:underline">
          <span className="line-clamp-2 max-w-64 break-words whitespace-normal">
            {row.original.document_title ?? row.original.url}
          </span>
        </a>
      ),
    }),
    column.accessor("extracted_at", {
      header: "Extracted",
      cell: ({ row }) => (
        <span className="whitespace-nowrap">
          {formatDateTime(row.original.extracted_at, timeZone)}
        </span>
      ),
    }),
  ]);
}

/** One button per record type, and one for all. */
function TypeButtons({
  value,
  onChange,
}: {
  value: RecordType | undefined;
  onChange: (type: RecordType | undefined) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {[undefined, ...recordTypes].map((option) => (
        <Button
          key={option ?? "all"}
          size="sm"
          variant={value === option ? "default" : "outline"}
          onClick={() => onChange(option)}
        >
          {option ? recordTypeLabels[option] : "All"}
        </Button>
      ))}
    </div>
  );
}

/**
 * The list's type and page, kept in the URL. A type's own page keeps its type
 * out of the URL, since the path already names it.
 */
function useRecordFilters(initialFilters: RecordSearch, fixedType: RecordType | undefined) {
  const [type, setType] = useState<RecordType | undefined>(fixedType ?? initialFilters.type);
  const [page, setPage] = useState(initialFilters.page ?? 1);
  const { deferred, isStale } = useUrlFilters(
    { type: fixedType ? undefined : type, page: page > 1 ? page : undefined },
    parseRecordSearch,
  );
  return {
    type,
    setType,
    page,
    setPage,
    deferred: fixedType ? { ...deferred, type: fixedType } : deferred,
    isStale,
  };
}

/**
 * Current records of one type, with the type's fields as columns; all types when none.
 * With `fixedType` it is that type's own page: its chosen columns, no type buttons.
 */
export function RecordsTable({
  initialFilters,
  timeZone,
  fixedType,
}: {
  initialFilters: RecordSearch;
  timeZone: string;
  fixedType?: RecordType;
}) {
  const { type, setType, page, setPage, deferred, isStale } = useRecordFilters(
    initialFilters,
    fixedType,
  );
  const { data: types } = useSuspenseQuery(recordTypesQuery(browserApi));
  const { data: records } = useSuspenseQuery(recordListQuery(browserApi, paged(deferred)));
  const fields = fixedType
    ? recordTypeColumns[fixedType]
    : (types.find((t) => t.record_type === deferred.type)?.fields ?? []);

  return (
    <div className="flex flex-col gap-4">
      {!fixedType && (
        <TypeButtons
          value={type}
          onChange={(next) => {
            setType(next);
            setPage(1);
          }}
        />
      )}
      <DataTable<RecordSummary>
        key={deferred.type ?? "all"}
        columns={recordColumns(fields, timeZone, deferred.type === undefined)}
        data={records.items}
        total={records.total}
        page={page}
        onPageChange={setPage}
        emptyMessage="No records of this type yet."
        className={cn(isStale && "opacity-60 transition-opacity")}
      />
    </div>
  );
}
