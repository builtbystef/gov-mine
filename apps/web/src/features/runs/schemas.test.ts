import { expect, test } from "vite-plus/test";

import { paged } from "@/lib/lists";

import { parsePageSearch } from "./schemas";

test("the first page is the URL without a page, and later pages ask for the right offset", () => {
  expect(parsePageSearch({})).toEqual({});
  expect(parsePageSearch({ page: "1" })).toEqual({});
  expect(paged(parsePageSearch({ page: "3" }))).toEqual({ limit: 50, offset: 100 });
});

test("a page that is not a number is ignored", () => {
  expect(parsePageSearch(new URLSearchParams("page=abc"))).toEqual({});
});
