import { expect, test } from "vite-plus/test";

import { findExcerpt } from "./highlight";

test("an excerpt is found across markdown emphasis and line breaks", () => {
  const text = "The board approved the **Parkdale Hub**\nplan for 1,000 homes.";
  const at = findExcerpt(text, "the Parkdale Hub plan for 1,000 homes");
  expect(at && text.slice(...at)).toBe("the **Parkdale Hub**\nplan for 1,000 homes");
  expect(findExcerpt(text, "2,000 homes")).toBeNull();
});
