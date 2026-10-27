import type { ReactNode } from "react";
import { cn } from "cn";

/**
 * One block of a settings page: heading and description in the left column,
 * the form or control in the right, with a rule between blocks. `wide`
 * stacks the heading above the content for things that need the full width,
 * such as tables.
 */
export function SettingsSections({ children }: { children: ReactNode }) {
  return <div className="flex flex-col divide-y">{children}</div>;
}

export function SettingsSection({
  title,
  description,
  wide = false,
  children,
}: {
  title: ReactNode;
  description?: ReactNode;
  wide?: boolean;
  children: ReactNode;
}) {
  return (
    <section
      className={cn(
        "grid gap-4 py-8 first:pt-0 last:pb-0",
        !wide && "md:grid-cols-[minmax(0,16rem)_minmax(0,1fr)] md:gap-x-12",
      )}
    >
      <div className="flex flex-col gap-1">
        <h2 className="text-base font-medium">{title}</h2>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      <div className={cn("flex min-w-0 flex-col gap-6", !wide && "md:max-w-md")}>{children}</div>
    </section>
  );
}

/** A labelled action with its button on the right: log out everywhere, leave, delete. */
export function ActionRow({
  title,
  description,
  destructive = false,
  children,
}: {
  title: ReactNode;
  description?: ReactNode;
  destructive?: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-between gap-x-6 gap-y-3 rounded-lg border p-4",
        destructive && "border-destructive/30 bg-destructive/3",
      )}
    >
      <div className="flex min-w-0 flex-1 basis-56 flex-col gap-0.5">
        <p className="text-sm font-medium">{title}</p>
        {description && <p className="text-sm text-muted-foreground">{description}</p>}
      </div>
      <div className="flex shrink-0 items-center gap-2">{children}</div>
    </div>
  );
}
