import { runP3ComputeReflections } from "@/api/pipelines/p3_signals/runner";
import { sql } from "@/lib/db";

export async function createNarrativeFromProjection(basketId: string, opts?: { title?: string; days?: number; maxDumps?: number }) {
  // Read-only projection to propose content (never mutate substrate/graph)
  const { projection, reflection } = await runP3ComputeReflections(basketId, { days: opts?.days, maxDumps: opts?.maxDumps, cache: false });

  const title = opts?.title || `Narrative — ${new Date().toISOString().slice(0,10)}`;
  const body =
`# ${title}

**Pattern:** ${reflection.pattern}
**Tension:** ${reflection.tension}
**Question:** ${reflection.question}

(Generated from recent graph window: ${projection.window.days}d / edgeCount=${projection.edgeCount})
`;

  const res = await sql/* sql */`
    select public.fn_document_create(${basketId}::uuid, ${title}, ${body}, 'narrative', '{}'::jsonb) as doc_id
  `;
  const docId = res.rows?.[0]?.doc_id || res.rows?.[0]?.fn_document_create;

  // Emit metrics
  await sql/* sql */`
    insert into public.pipeline_metrics (pipeline, basket_id, doc_id, counts, dims)
    values ('p4', ${basketId}::uuid, ${docId}::uuid,
            ${JSON.stringify({ doc_created: 1 })}::jsonb,
            ${JSON.stringify({ document_type: 'narrative' })}::jsonb);
  `;

  return { docId, title };
}