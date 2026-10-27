import { expect, test } from "vite-plus/test";

import { formatCost, formatDuration } from "./numbers";

test("durations read as the largest two units", () => {
  expect(formatDuration(null)).toBe("–");
  expect(formatDuration(45.6)).toBe("45s");
  expect(formatDuration(725)).toBe("12m 5s");
  expect(formatDuration(7380)).toBe("2h 3m");
});

test("costs show cents, or the first figures of a fraction of a cent", () => {
  expect(formatCost("0")).toBe("$0");
  expect(formatCost("1.234500000000")).toBe("$1.23");
  expect(formatCost("0.000123400000")).toBe("$0.00012");
});
