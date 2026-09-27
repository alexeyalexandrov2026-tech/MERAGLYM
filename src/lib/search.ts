/**
 * Search over the OSINT framework tree, shared by the web (PostgreSQL) and
 * desktop (SQLite) builds so both behave identically.
 *
 * The database narrows candidates with a case-insensitive "contains" on each
 * query term; ranking happens here:
 *  - plural terms are reduced to their singular form ("apps" -> "app"), and
 *    because matching is by substring, "app" still matches "apps";
 *  - nodes containing every term rank first; if none contain every term, the
 *    best partial matches are returned instead of nothing;
 *  - rare terms count for more than common ones, name matches outrank
 *    description matches, and an exact or phrase match on the name (e.g. the
 *    "Dating" category) ranks highest.
 */

export interface SearchableNode {
  name: string;
  description: string | null;
}

const STOPWORDS = new Set([
  "a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with",
]);

const MAX_TERMS = 8;
export const MAX_RESULTS = 100;

/** Reduce common English plurals to their singular form. */
export function stem(word: string): string {
  if (word.length > 4 && word.endsWith("ies")) return `${word.slice(0, -3)}y`;
  if (word.length > 4 && /(ses|xes|zes|ches|shes)$/.test(word)) return word.slice(0, -2);
  if (
    word.length > 3 &&
    word.endsWith("s") &&
    !/(ss|us|is)$/.test(word)
  ) {
    return word.slice(0, -1);
  }
  return word;
}

/** Split a query into lowercase, de-duplicated, stemmed search terms. */
export function toSearchTerms(query: string): string[] {
  const terms: string[] = [];
  for (const raw of query.toLowerCase().split(/[^\p{L}\p{N}]+/u)) {
    if (raw.length < 2 || STOPWORDS.has(raw)) continue;
    const term = stem(raw);
    if (!terms.includes(term)) terms.push(term);
    if (terms.length === MAX_TERMS) break;
  }
  return terms;
}

/** Rank candidate nodes for a query. `terms` must come from `toSearchTerms`. */
export function rankNodes<T extends SearchableNode>(
  nodes: T[],
  query: string,
  terms: string[],
): T[] {
  if (terms.length === 0) return [];
  const phrase = query.trim().toLowerCase();

  const lowered = nodes.map((node) => ({
    node,
    name: node.name.toLowerCase(),
    description: (node.description ?? "").toLowerCase(),
  }));

  // Weight each term by how rare it is among the candidates, so a distinctive
  // word ("dating") counts for more than a common one ("site").
  const weight = new Map<string, number>();
  for (const term of terms) {
    const df = lowered.filter(
      (n) => n.name.includes(term) || n.description.includes(term),
    ).length;
    weight.set(term, df > 0 ? Math.log(1 + lowered.length / df) : 0);
  }

  const scored: { node: T; matched: number; score: number }[] = [];
  for (const { node, name, description } of lowered) {
    let matched = 0;
    let score = 0;
    for (const term of terms) {
      const w = weight.get(term) ?? 0;
      if (name.includes(term)) {
        matched += 1;
        score += 1.5 * w;
      } else if (description.includes(term)) {
        matched += 1;
        score += w;
      }
    }
    if (matched === 0) continue;

    if (name === phrase) score += 10;
    else if (name.includes(phrase)) score += 5;
    if (name.startsWith(terms[0])) score += 2;

    scored.push({ node, matched, score });
  }

  // Prefer nodes that contain every term; otherwise fall back to the best
  // partial matches so a query never comes back empty when anything matches.
  const complete = scored.filter((s) => s.matched === terms.length);
  const pool = complete.length > 0 ? complete : scored;

  pool.sort(
    (a, b) =>
      b.matched - a.matched ||
      b.score - a.score ||
      a.node.name.length - b.node.name.length ||
      a.node.name.localeCompare(b.node.name),
  );

  return pool.slice(0, MAX_RESULTS).map((s) => s.node);
}
