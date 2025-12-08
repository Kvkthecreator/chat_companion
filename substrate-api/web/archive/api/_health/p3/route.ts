import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";

export async function GET() {
  const supabase = createRouteHandlerClient({ cookies });
  
  const { data, error } = await supabase
    .from('pipeline_offsets')
    .select('pipeline_name, last_event_id, last_event_ts, updated_at')
    .eq('pipeline_name', 'p3_reflections_consumer')
    .single();

  if (error) {
    return NextResponse.json({}, { status: 200 }); // Return empty object if not found
  }

  return NextResponse.json(data || {});
}