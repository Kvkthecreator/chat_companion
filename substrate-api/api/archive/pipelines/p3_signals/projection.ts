import { sql } from "@/lib/db";

export type ProjectionParams = {
  basketId: string;
  days?: number;        // default 14
  maxDumps?: number;    // default 50
};

export async function loadProjection(params: ProjectionParams) {
  const days = params.days ?? 14;
  const maxDumps = params.maxDumps ?? 50;

  // 1) window: recent dumps by time (and cap)
  const dumps = await sql/* sql */`
    select id from public.raw_dumps
    where basket_id = ${params.basketId}::uuid
      and created_at >= now() - (${days} || ' days')::interval
    order by created_at desc
    limit ${maxDumps};
  `;
  const dumpIds: string[] = dumps.rows.map((r: any) => r.id);
  if (!dumpIds.length) return { entities: [], topics: [], intents: [], cues: [], tasks: [], edges: [], window: {days, maxDumps} };

  // 2) context_items in window (by origin_ref or raw_dump_id)
  const items = await sql/* sql */`
    select id, type, content as label, normalized_label
    from public.context_items
    where basket_id = ${params.basketId}::uuid
      and (raw_dump_id = any(${dumpIds}::uuid[]) or
           (origin_ref is not null and exists (
              select 1
              from jsonb_array_elements(origin_ref) as o
              where (o->>'type')='dump' and (o->>'id')::uuid = any(${dumpIds}::uuid[])
           )))
  `;

  // 3) edges touching those nodes (directed)
  const edges = await sql/* sql */`
    select from_type, from_id, relationship_type, to_type, to_id
    from public.substrate_relationships
    where basket_id = ${params.basketId}::uuid
      and (
        (from_type='raw_dump' and from_id = any(${dumpIds}::uuid[])) or
        (to_type='raw_dump' and to_id = any(${dumpIds}::uuid[])) or
        (from_type='context_item' and from_id in (select id from public.context_items where basket_id=${params.basketId}::uuid)) or
        (to_type='context_item'   and to_id   in (select id from public.context_items where basket_id=${params.basketId}::uuid))
      )
  `;

  // Partition items by type
  const byType = (t: string) => items.rows.filter((r: any) => r.type === t);
  return {
    entities: byType("entity"),
    topics: byType("topic"),
    intents: byType("intent"),
    cues: byType("cue"),
    tasks: byType("task"),
    edges: edges.rows,
    window: { days, maxDumps }
  };
}