// DEPRECATED: This legacy pipeline file should use canonical P2 Graph Agent
// For now, removing invalid import to fix build error
// TODO: Remove this file and use canonical pipeline agents instead
import { Edge, edgesFromDumpCreated, edgesFromContextBulkTagged, edgesFromBlockEvent } from "./rules";

// In your stack, P1 emits machine-consumable signals to `public.events` with free-form 'kind'
const KINDS = new Set(["dump.created","context.bulk_tagged","block.proposed","block.revised","block.accepted"]);

async function upsertEdges(basketId: string, edges: Edge[], idemKey?: string) {
  // DEPRECATED: This function should use canonical P2 Graph Agent
  // Placeholder implementation to prevent build errors
  console.warn('DEPRECATED: upsertEdges should use canonical P2 Graph Agent');
  return { created: 0, ignored: 0 };
}

export async function handleEvent(ev: any) {
  const kind: string = ev.kind || "";
  if (!KINDS.has(kind)) return { skipped: true };

  let edges: Edge[] = [];
  if (kind === "dump.created") edges = edgesFromDumpCreated(ev);
  else if (kind === "context.bulk_tagged") edges = edgesFromContextBulkTagged(ev);
  else if (kind.startsWith("block.")) edges = edgesFromBlockEvent(ev);

  const basketId = ev.basket_id || ev.payload?.basket_id;
  const idem = ev.payload?.idem_key;
  const result = await upsertEdges(basketId, edges, idem);
  
  // DEPRECATED: Metrics emission should use canonical P2 Graph Agent
  console.warn('DEPRECATED: Pipeline metrics should use canonical P2 Graph Agent');
  
  return { kind, count: edges.length, result };
}