import type { RunOutput } from "@gov-mine/api-client";

import { formatCost, formatDuration } from "@/lib/formatting/numbers";
import { cn } from "@/lib/utils";

/** A run's tallies as stat tiles, each as the API counted it. */
export function RunCounts({ run }: { run: RunOutput }) {
  const { counts } = run;
  const tiles = [
    { label: "Fetched", value: counts.fetched },
    { label: "Not modified", value: counts.not_modified },
    { label: "Skipped", value: counts.skipped },
    { label: "Blocked", value: counts.blocked },
    { label: "Failed", value: counts.failed, alert: counts.failed > 0 },
    { label: "Snapshots", value: counts.snapshots },
    { label: "Elapsed", value: formatDuration(run.elapsed_seconds) },
    { label: "Cost", value: formatCost(counts.cost) },
  ];
  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
      {tiles.map((tile) => (
        <div key={tile.label} className="rounded-lg border bg-card px-3 py-2.5">
          <dt className="text-xs text-muted-foreground">{tile.label}</dt>
          <dd
            className={cn("text-xl font-semibold tabular-nums", tile.alert && "text-destructive")}
          >
            {tile.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
