// Map upstream events to edges. Keep it tiny & deterministic.
// Your rel_type vocabulary lives in docs/YARNNN_GRAPH_CANON.md.

export type Edge = {
  from_type: string; from_id: string;
  to_type: string;   to_id: string;
  relationship_type: string;
  description?: string;
  strength?: number;
};

export function edgesFromDumpCreated(ev: any): Edge[] {
  // Example: link dump -> basket with 'belongs_to'
  return [{
    from_type: "raw_dump",
    from_id: ev.payload?.dump_id || ev.ref_id || ev.dump_id,
    to_type: "basket",
    to_id: ev.payload?.basket_id || ev.basket_id,
    relationship_type: "belongs_to",
    description: "dump is scoped to basket"
  }];
}

export function edgesFromContextBulkTagged(ev: any): Edge[] {
  // Expect ev.payload to include item IDs or we re-query by dump_id.
  const dumpId = ev.payload?.dump_id;
  const basketId = ev.payload?.basket_id || ev.basket_id;
  const items: any[] = ev.payload?.items || []; // if you emit them; otherwise query
  return items.map((it) => ({
    from_type: "context_item",
    from_id: it.id,
    to_type: "raw_dump",
    to_id: dumpId,
    relationship_type: "mentions"
  }));
}

export function edgesFromBlockEvent(ev: any): Edge[] {
  const basketId = ev.payload?.basket_id || ev.basket_id;
  const blockId = ev.payload?.block_id || ev.ref_id;
  // Example: block derived_from dump (if payload contains dump_id)
  if (ev.payload?.dump_id) {
    return [{
      from_type: "block",
      from_id: blockId,
      to_type: "raw_dump",
      to_id: ev.payload.dump_id,
      relationship_type: "derived_from"
    }];
  }
  return [];
}