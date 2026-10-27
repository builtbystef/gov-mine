import type { Metadata } from "next";

import { FormPage } from "@/components/shared/layout/form-page";
import { InstitutionForm } from "@/features/institutions/components/institution-form";

export const metadata: Metadata = { title: "Add institution" };

export default function NewInstitutionPage() {
  return (
    <FormPage>
      <InstitutionForm />
    </FormPage>
  );
}
