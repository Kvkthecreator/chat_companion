import { sql } from "@/lib/db";
import { runP3ComputeReflections } from "./runner";

const PIPELINE = "p3_reflections_consumer";
const BATCH = 50;

async function getOffset() {
  const res = await sql/* sql */`
    select pipeline_name, last_event_id, last_event_ts
    from public.pipeline_offsets
    where pipeline_name = ${PIPELINE}
  `;
  return res.rows?.[0] || null;
}

async function setOffset(eventId: string, ts: string) {
  await sql/* sql */`
    insert into public.pipeline_offsets (pipeline_name, last_event_id, last_event_ts)
    values (${PIPELINE}, ${eventId}::uuid, ${ts}::timestamptz)
    on conflict (pipeline_name) do update
      set last_event_id = excluded.last_event_id,
          last_event_ts = excluded.last_event_ts,
          updated_at = now();
  `;
}

async function fetchEventsSince(lastTs?: string, lastId?: string) {
  // Read from view; keep stable ordering by ts then id
  const res = await sql/* sql */`
    select id, basket_id, kind, payload, ts
    from public.v_events_rel_bulk
    where (${lastTs}::timestamptz is null or ts > ${lastTs}::timestamptz)
    order by ts asc
    limit ${BATCH}
  `;
  return res.rows || [];
}

export async function runOnce() {
  const off = await getOffset();
  const events = await fetchEventsSince(off?.last_event_ts, off?.last_event_id);
  if (!events.length) return { processed: 0, advanced: false };

  let processed = 0;
  for (const ev of events) {
    const basketId = ev.basket_id || ev.payload?.basket_id;
    if (!basketId) continue;

    // Run reflections with cache=true; idempotent via meta hash
    await runP3ComputeReflections(basketId, { cache: true });
    await setOffset(ev.id, ev.ts);
    processed++;
  }
  return { processed, advanced: true, last: events[events.length - 1].id };
}