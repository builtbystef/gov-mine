import { expect, test } from "vite-plus/test";

import { paged } from "@/lib/lists";

import { parseDocumentSearch } from "./schemas";

test("the Documents list reads its filters from the URL and drops the ones it does not know", () => {
  const institution = "01a17d97-78ba-71bd-b86a-54029e1b2410";
  expect(
    paged(parseDocumentSearch({ institution, type: "projects", since: "2024-01-01", page: "2" })),
  ).toEqual({ institution, type: "projects", since: "2024-01-01", limit: 50, offset: 50 });
  expect(parseDocumentSearch({ institution: "x", type: "memos", since: "2024-13-40" })).toEqual({});
});
