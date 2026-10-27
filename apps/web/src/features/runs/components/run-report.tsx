import type { RunReport as Report } from "@gov-mine/api-client";
import type { ReactNode } from "react";

import { formatCost, formatDuration } from "@/lib/formatting/numbers";
import { cn } from "@/lib/utils";

function Tile({
  label,
  value,
  note,
  alert = false,
}: {
  label: string;
  value: ReactNode;
  note?: ReactNode;
  alert?: boolean;
}) {
  return (
    <div className="rounded-lg border bg-card px-3 py-2.5">
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={cn("text-xl font-semibold tabular-nums", alert && "text-destructive")}>
        {value}
      </dd>
      {note && <dd className="text-xs text-muted-foreground">{note}</dd>}
    </div>
  );
}

/** The run's report as stat tiles, each a number the API read from its logs. */
export function RunReport({ report }: { report: Report }) {
  const elapsed = report.elapsed_seconds ?? report.run.elapsed_seconds;
  return (
    <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
      <Tile
        label="Time"
        value={formatDuration(elapsed)}
        note={report.elapsed_seconds === null && elapsed !== null ? "So far" : undefined}
      />
      <Tile label="Requests" value={report.requests_sent} note="Retries included" />
      <Tile
        label="Files processed"
        value={report.files_processed}
        alert={report.files_failed > 0}
        note={
          [
            report.files_failed > 0 && `${report.files_failed} failed`,
            report.files_parsing > 0 && `${report.files_parsing} parsing`,
          ]
            .filter(Boolean)
            .join(", ") || `of ${report.snapshots_written} snapshots`
        }
      />
      <Tile
        label="Documents"
        value={report.documents_new}
        note={`New; ${report.documents_changed} changed`}
      />
      <Tile label="Paid calls" value={report.paid_calls} />
      <Tile
        label="Cost"
        value={report.reported_cost === null ? "–" : formatCost(report.reported_cost)}
        note="Reported by OpenRouter"
      />
      <Tile label="Cost" value={formatCost(report.estimated_cost)} note="Estimated" />
    </dl>
  );
}
