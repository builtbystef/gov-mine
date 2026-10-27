import { expect, test } from "vite-plus/test";

import { paged } from "@/lib/lists";

import { parsePageSearch, parseRunSearch } from "./schemas";

test("the first page is the URL without a page, and later pages ask for the right offset", () => {
  expect(parsePageSearch({})).toEqual({});
  expect(parsePageSearch({ page: "1" })).toEqual({});
  expect(paged(parsePageSearch({ page: "3" }))).toEqual({ limit: 50, offset: 100 });
});

test("a page that is not a number is ignored", () => {
  expect(parsePageSearch(new URLSearchParams("page=abc"))).toEqual({});
});

test("the run page reads its tab, outcome and search from the URL", () => {
  expect(parseRunSearch({})).toEqual({});
  expect(parseRunSearch({ tab: "snapshots", page: "2" })).toEqual({ tab: "snapshots", page: 2 });
  expect(parseRunSearch(new URLSearchParams("outcome=skipped_scope&q=%20pdf%20"))).toEqual({
    outcome: "skipped_scope",
    q: "pdf",
  });
});

test("the run page drops a tab, outcome or search it does not know", () => {
  expect(parseRunSearch({ tab: "fetches" })).toEqual({});
  expect(parseRunSearch({ tab: "records", outcome: "nonsense", q: "" })).toEqual({});
});
