import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";

export async function GET(req: Request) {
  const supabase = createRouteHandlerClient({ cookies });
  const { searchParams } = new URL(req.url);
  const basketId = searchParams.get("basket_id");
  
  if (!basketId) {
    return NextResponse.json({ error: "basket_id required" }, { status: 400 });
  }

  try {
    const { data, error } = await supabase
      .from('v_kpi_basket_recent')
      .select('*')
      .eq('basket_id', basketId);

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json(data || []);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch basket KPIs' }, { status: 500 });
  }
}