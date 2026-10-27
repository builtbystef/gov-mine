import { expect, test } from "vite-plus/test";

import { fieldLabel, formatValue, parseRecordSearch } from "./schemas";

test("the record type and page come from the URL, and an unknown type is dropped", () => {
  expect(parseRecordSearch({ type: "project", page: "2" })).toEqual({ type: "project", page: 2 });
  expect(parseRecordSearch(new URLSearchParams("type=budget"))).toEqual({});
});

test("fields and values read as words", () => {
  expect(fieldLabel("start_date")).toBe("Start date");
  expect(formatValue(["CreateTO", "City of Toronto"])).toBe("CreateTO, City of Toronto");
  expect(formatValue(1250000)).toBe("1,250,000");
  expect(formatValue(null)).toBe("");
});
