/**
 * Where an excerpt is in a page's markdown, as [start, end), or null. The
 * excerpt's words must appear in order, separated by anything that is not a
 * letter or digit, so markdown emphasis and line breaks do not hide it.
 */
export function findExcerpt(text: string, excerpt: string): [number, number] | null {
  const words = excerpt
    .split(/[^\p{L}\p{N}]+/u)
    .filter(Boolean)
    .map((word) => word.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  if (words.length === 0) return null;
  const match = new RegExp(words.join("[^\\p{L}\\p{N}]+"), "iu").exec(text);
  return match ? [match.index, match.index + match[0].length] : null;
}
