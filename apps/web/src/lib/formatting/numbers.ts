/** Seconds as "45s", "12m 5s" or "2h 3m"; a dash for null. */
export function formatDuration(seconds: number | null): string {
  if (seconds === null) return "–";
  const whole = Math.floor(seconds);
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const rest = whole % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${rest}s`;
  return `${rest}s`;
}

/** A cost in US dollars as the API sends it (a decimal string), to the cent or the first figure. */
export function formatCost(cost: string): string {
  const value = Number(cost);
  if (value === 0) return "$0";
  if (value >= 0.01) return `$${value.toFixed(2)}`;
  return `$${value.toPrecision(2)}`;
}
