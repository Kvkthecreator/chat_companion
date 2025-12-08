import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";

export async function GET() {
  const supabase = createRouteHandlerClient({ cookies });
  
  try {
    const [p3OffResult, lastTimelineResult] = await Promise.all([
      supabase
        .from('pipeline_offsets')
        .select('pipeline_name, last_event_id, last_event_ts, updated_at')
        .eq('pipeline_name', 'p3_reflections_consumer')
        .single(),
      supabase
        .from('timeline_events')
        .select('kind, ts')
        .order('ts', { ascending: false })
        .limit(1)
        .single()
    ]);

    return NextResponse.json({
      p3_consumer: p3OffResult.data || null,
      latest_timeline: lastTimelineResult.data || null
    });
  } catch (error) {
    // Return empty data if queries fail (graceful degradation)
    return NextResponse.json({
      p3_consumer: null,
      latest_timeline: null
    });
  }
}