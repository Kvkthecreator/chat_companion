import { NextRequest } from "next/server";
import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { checkBasketAccess } from "@/lib/baskets/access";

interface RouteParams {
  id: string;
  eventId: string;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<RouteParams> }
) {
  try {
    const { id: basketId, eventId } = await params;
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check basket access
    await checkBasketAccess(supabase, basketId);
    
    // Fetch timeline event details
    const { data: event, error } = await supabase
      .from('timeline_events')
      .select(`
        id,
        basket_id,
        kind,
        ref_id,
        preview,
        payload,
        created_at,
        workspace_id
      `)
      .eq('id', eventId)
      .eq('basket_id', basketId)
      .single();
    
    if (error || !event) {
      return Response.json({ error: 'Timeline event not found' }, { status: 404 });
    }
    
    // Rename 'kind' to 'event_kind' for consistency
    return Response.json({
      ...event,
      event_kind: event.kind
    });
  } catch (error: any) {
    console.error('Failed to fetch timeline event:', error);
    return Response.json(
      { error: error.message || 'Failed to fetch timeline event' },
      { status: error.status || 500 }
    );
  }
}