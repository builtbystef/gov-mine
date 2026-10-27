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

/** Sections whose pages are a list and an item: the list's title, then an item's. */
const listSections: Record<string, [string, string]> = {
  runs: ["Runs", "Run"],
  records: ["Records", "Record"],
  documents: ["Documents", "Document"],
  snapshots: ["Snapshots", "Snapshot"],
  webpages: ["Webpages", "Webpage"],
};

export function titleFor(pathname: string): string | null {
  const [section, id, action] = pathname.split("/").filter(Boolean);
  if (section === undefined) return "Home";
  if (section === "institutions") {
    if (id === undefined) return "Institutions";
    if (id === "new") return "Add institution";
    return action === "edit" ? "Edit institution" : "Institution";
  }
  const titles = listSections[section];
  if (titles === undefined) return null;
  return id === undefined ? titles[0] : titles[1];
}
