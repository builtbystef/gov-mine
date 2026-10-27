import { expect, test } from "vite-plus/test";

import { emptyInstitution, institutionFormSchema } from "./schemas";

test("a filled form becomes the API's input, with empty fields as null", () => {
  const result = institutionFormSchema.parse({
    ...emptyInstitution,
    name: " City of Example ",
    website_url: "https://www.example.gov/",
    country_code: "us",
  });

  expect(result).toEqual({
    name: "City of Example",
    institution_type: "city",
    website_url: "https://www.example.gov/",
    country_code: "US",
    state: null,
    city: null,
  });
});

test("a website that is not http or https, or a missing name, is refused", () => {
  const result = institutionFormSchema.safeParse({
    ...emptyInstitution,
    website_url: "ftp://example.gov/",
  });

  expect(result.success).toBe(false);
  const fields = result.error?.issues.map((issue) => issue.path[0]);
  expect(fields).toEqual(expect.arrayContaining(["name", "website_url"]));
});
