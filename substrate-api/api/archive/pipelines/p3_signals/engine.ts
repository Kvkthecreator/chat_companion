import crypto from "crypto";

function hashInputs(obj: any) {
  const s = JSON.stringify(obj);
  return crypto.createHash("sha256").update(s).digest("hex");
}

export type Reflection = { pattern: string; tension: string; question: string; meta_derived_from: string };

export function computeReflections(projection: {
  entities: any[]; topics: any[]; intents: any[]; cues: any[]; tasks: any[]; edges: any[];
}) : Reflection {
  // super-simple heuristic baselines; replace with richer logic later
  const topEntity = tallyTopLabel(projection.entities);
  const topTopic  = tallyTopLabel(projection.topics);
  const topIntent = tallyTopLabel(projection.intents);

  const pattern = topTopic
    ? `Rising focus on ${topTopic}`
    : (topEntity ? `Entity ${topEntity} dominates recent memory` : `Recent memory lacks clear topic focus`);

  const tension = (topIntent && topTopic)
    ? `Intent "${topIntent}" may not align with topic "${topTopic}" yet`
    : `Intent signals are weak—consider clarifying near-term goals`;

  const question = (topTopic)
    ? `What concrete step advances "${topTopic}" this week?`
    : `What is our immediate priority to reduce ambiguity?`;

  const meta_derived_from = hashInputs({
    e: projection.entities.map(x => x.normalized_label || x.label).sort(),
    t: projection.topics.map(x => x.normalized_label || x.label).sort(),
    i: projection.intents.map(x => x.normalized_label || x.label).sort(),
    edgeCount: projection.edges.length
  });

  return { pattern, tension, question, meta_derived_from };
}

function tallyTopLabel(rows: any[]): string | null {
  const m = new Map<string, number>();
  for (const r of rows) {
    const k = (r.normalized_label || r.label || "").toLowerCase();
    if (!k) continue;
    m.set(k, (m.get(k) || 0) + 1);
  }
  let best: string | null = null, score = 0;
  for (const [k, v] of m.entries()) if (v > score) { best = k; score = v; }
  return best;
}