import type { Metadata } from "next";

import { RecordTypeList } from "@/features/records/components/record-type-list";
import type { SearchParams } from "@/lib/lists";

export const metadata: Metadata = { title: "Contacts" };

export default function Page({ searchParams }: { searchParams: Promise<SearchParams> }) {
  return <RecordTypeList type="contact" searchParams={searchParams} />;
}
