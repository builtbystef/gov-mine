"use client";

import { usePathname } from "next/navigation";

/**
 * The title of the current page, shown in the shell header. It is derived from
 * the URL, which is only known at request time, so it streams in behind a
 * <Suspense> while the rest of the shell is prerendered.
 */
export function PageTitle() {
  const title = titleFor(usePathname());
  return title ? <h1 className="truncate text-sm font-medium">{title}</h1> : null;
}

export function titleFor(pathname: string): string | null {
  const [section, id, action] = pathname.split("/").filter(Boolean);
  switch (section) {
    case undefined:
      return "Home";
    case "institutions":
      if (id === undefined) return "Institutions";
      return id === "new"
        ? "Add institution"
        : action === "edit"
          ? "Edit institution"
          : "Institution";
    case "runs":
      return id === undefined ? "Runs" : "Run";
    case "snapshots":
      return "Snapshot";
    case "webpages":
      return "Webpage";
    default:
      return null;
  }
}
