import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { FormPage } from "@/components/shared/layout/form-page";
import { DetailSkeleton } from "@/components/shared/skeletons";
import { InstitutionForm } from "@/features/institutions/components/institution-form";
import { unwrap } from "@/lib/api/errors";
import { api } from "@/lib/api/server-client";

export const metadata: Metadata = { title: "Edit institution" };

type Params = Promise<{ id: string }>;

export default function EditInstitutionPage({ params }: { params: Params }) {
  return (
    <FormPage>
      <Suspense fallback={<DetailSkeleton />}>
        <EditContent params={params} />
      </Suspense>
    </FormPage>
  );
}

async function EditContent({ params }: { params: Params }) {
  const { id } = await params;
  const result = await api.GET("/institutions/{institution_id}", {
    params: { path: { institution_id: id } },
  });
  if (result.response.status === 404 || result.response.status === 422) notFound();
  return <InstitutionForm institution={unwrap(result)} />;
}
