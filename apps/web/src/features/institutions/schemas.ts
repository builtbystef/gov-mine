import type { InstitutionOutput, InstitutionType } from "@gov-mine/api-client";
import { z } from "zod";

import { optionalText, requiredText, text } from "@/lib/validation";

export const institutionTypeLabels = {
  state: "State",
  state_agency: "State agency",
  county: "County",
  city: "City",
  police_agency: "Police agency",
  fire_department: "Fire department",
  special_district: "Special district",
  k12_district: "K-12 district",
  higher_education: "Higher education",
  municipal_agency: "Municipal agency",
} as const satisfies Record<InstitutionType, string>;

const institutionTypes = Object.keys(institutionTypeLabels) as [
  InstitutionType,
  ...InstitutionType[],
];

/** The Add and Edit forms: strings in, the API's `InstitutionInput` out. */
export const institutionFormSchema = z.object({
  name: requiredText("Name", 300),
  institution_type: z.enum(institutionTypes, "Choose a type"),
  website_url: text.pipe(
    z.httpUrl("Enter a URL starting with http:// or https://").max(2048, "The URL is too long"),
  ),
  country_code: text
    .toUpperCase()
    .pipe(z.union([z.literal(""), z.string().regex(/^[A-Z]{2}$/, "Two letters, like US")]))
    .transform((value) => (value === "" ? null : value)),
  state: optionalText(100),
  city: optionalText(100),
});

export type InstitutionFormValues = z.input<typeof institutionFormSchema>;

export const emptyInstitution: InstitutionFormValues = {
  name: "",
  institution_type: "city",
  website_url: "",
  country_code: "",
  state: "",
  city: "",
};

export function institutionFormValues(institution: InstitutionOutput): InstitutionFormValues {
  return {
    name: institution.name,
    institution_type: institution.institution_type,
    website_url: institution.website_url,
    country_code: institution.country_code ?? "",
    state: institution.state ?? "",
    city: institution.city ?? "",
  };
}
