"use client";

import { useEffect } from "react";

/**
 * Scrolls the marked excerpt into view once the page has loaded. The `#excerpt`
 * fragment alone scrolls only the text box, not the page around it.
 */
export function ScrollToExcerpt() {
  useEffect(() => {
    document.getElementById("excerpt")?.scrollIntoView({ block: "center" });
  }, []);
  return null;
}
