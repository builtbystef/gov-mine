"use client";

import type { InstitutionOutput } from "@gov-mine/api-client";
import { revalidateLogic } from "@tanstack/react-form";
import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import {
  Form,
  FormActions,
  FormError,
  FormSection,
  FormSections,
  useAppForm,
} from "@/components/shared/form";
import { Button } from "@/components/ui/button";
import { browserApi } from "@/lib/api/client";
import { ApiError, errorMessage, unwrap } from "@/lib/api/errors";

import { institutionKeys } from "../queries";
import {
  emptyInstitution,
  institutionFormSchema,
  institutionFormValues,
  institutionTypeLabels,
} from "../schemas";

const typeOptions = Object.entries(institutionTypeLabels).map(([value, label]) => ({
  value,
  label,
}));

/** Adds an institution, or edits `institution` when given. Saving makes its host a crawl domain. */
export function InstitutionForm({ institution }: { institution?: InstitutionOutput }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const form = useAppForm({
    defaultValues: institution ? institutionFormValues(institution) : emptyInstitution,
    validationLogic: revalidateLogic(),
    validators: { onDynamic: institutionFormSchema },
    onSubmit: async ({ value, formApi }) => {
      setError(null);
      const body = institutionFormSchema.parse(value);
      try {
        const saved = unwrap(
          institution
            ? await browserApi.PUT("/institutions/{institution_id}", {
                params: { path: { institution_id: institution.id } },
                body,
              })
            : await browserApi.POST("/institutions", { body }),
        );
        await queryClient.invalidateQueries({ queryKey: institutionKeys.all });
        toast.success(institution ? `Saved ${saved.name}` : `Added ${saved.name}`);
        router.push("/institutions");
      } catch (caught) {
        if (caught instanceof ApiError) {
          for (const [field, message] of Object.entries(caught.fields)) {
            if (field in value) {
              formApi.setFieldMeta(field as keyof typeof value, (meta) => ({
                ...meta,
                isTouched: true,
                errorMap: { ...meta.errorMap, onServer: message },
              }));
            }
          }
        }
        setError(errorMessage(caught));
      }
    },
  });

  return (
    <Form form={form} warnOnLeave>
      <FormError message={error} />
      <FormSections>
        <FormSection title="Institution" description="The public body and the website to crawl.">
          <form.AppField name="name">{(f) => <f.TextField label="Name" required />}</form.AppField>
          <form.AppField name="institution_type">
            {(f) => <f.SelectField label="Type" required options={typeOptions} />}
          </form.AppField>
          <form.AppField name="website_url">
            {(f) => (
              <f.TextField
                label="Website"
                required
                type="url"
                placeholder="https://www.example.gov/"
                description="The crawl starts here and stays under this address."
              />
            )}
          </form.AppField>
        </FormSection>
        <FormSection title="Location" description="For display only.">
          <form.AppField name="country_code">
            {(f) => <f.TextField label="Country code" placeholder="US" maxLength={2} />}
          </form.AppField>
          <form.AppField name="state">{(f) => <f.TextField label="State" />}</form.AppField>
          <form.AppField name="city">{(f) => <f.TextField label="City" />}</form.AppField>
        </FormSection>
      </FormSections>
      <FormActions>
        <Button variant="outline" render={<Link href="/institutions" />} nativeButton={false}>
          Cancel
        </Button>
        <form.AppForm>
          <form.SubmitButton requireChanges={institution !== undefined}>
            {institution ? "Save" : "Add institution"}
          </form.SubmitButton>
        </form.AppForm>
      </FormActions>
    </Form>
  );
}
