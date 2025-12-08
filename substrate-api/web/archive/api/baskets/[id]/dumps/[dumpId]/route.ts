import { NextRequest } from "next/server";
import { createRouteHandlerClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { checkBasketAccess } from "@/lib/baskets/access";

interface RouteParams {
  id: string;
  dumpId: string;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<RouteParams> }
) {
  try {
    const { id: basketId, dumpId } = await params;
    const supabase = createRouteHandlerClient({ cookies });
    
    // Check basket access
    await checkBasketAccess(supabase, basketId);
    
    // Fetch raw dump details
    const { data: dump, error } = await supabase
      .from('raw_dumps')
      .select(`
        id,
        basket_id,
        body_md,
        file_url,
        processing_status,
        processed_at,
        created_at,
        metadata
      `)
      .eq('id', dumpId)
      .eq('basket_id', basketId)
      .single();
    
    if (error || !dump) {
      return Response.json({ error: 'Raw dump not found' }, { status: 404 });
    }
    
    return Response.json(dump);
  } catch (error: any) {
    console.error('Failed to fetch raw dump:', error);
    return Response.json(
      { error: error.message || 'Failed to fetch raw dump' },
      { status: error.status || 500 }
    );
  }
}