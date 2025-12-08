import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";

export async function GET() {
  const supabase = createRouteHandlerClient({ cookies });
  
  try {
    const { data, error } = await supabase
      .from('v_kpi_24h')
      .select('*');

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json(data || []);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch KPI summary' }, { status: 500 });
  }
}