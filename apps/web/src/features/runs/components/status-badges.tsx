import type { FetchOutcome, RunStatus } from "@gov-mine/api-client";
import type { ComponentProps } from "react";

import { Badge } from "@/components/ui/badge";

type Variant = NonNullable<ComponentProps<typeof Badge>["variant"]>;

/** Status and outcome values as the API sends them, in words. */
function label(value: string): string {
  const words = value.replaceAll("_", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

const runStatusVariants: Record<RunStatus, Variant> = {
  queued: "outline",
  running: "info",
  finished: "success",
  failed: "destructive",
  cancelled: "outline",
};

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return <Badge variant={runStatusVariants[status]}>{label(status)}</Badge>;
}

/** Fetched and its kin are what a crawl is for; refusals are neutral; failures stand out. */
function outcomeVariant(outcome: FetchOutcome): Variant {
  if (outcome.startsWith("failed_")) return "destructive";
  if (outcome === "fetched") return "success";
  if (outcome === "not_modified" || outcome === "unchanged") return "info";
  return "outline";
}

export function outcomeLabel(outcome: FetchOutcome): string {
  return label(outcome);
}

export function FetchOutcomeBadge({ outcome }: { outcome: FetchOutcome }) {
  return <Badge variant={outcomeVariant(outcome)}>{label(outcome)}</Badge>;
}
