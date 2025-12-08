import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { plan } from "@/app/api/export_agent/agent";

export async function POST(req: Request) {
  const supabase = createRouteHandlerClient({ cookies });
  
  try {
    const body = await req.json();
    const { basketId, format = 'markdown', docId, includeProvenance = false } = body;

    if (!basketId) {
      return NextResponse.json({ error: "basketId required" }, { status: 400 });
    }

    if (!['markdown', 'html'].includes(format)) {
      return NextResponse.json({ error: "format must be 'markdown' or 'html'" }, { status: 400 });
    }

    const exportPlan = await plan({
      basketId,
      format,
      docId,
      includeProvenance
    });

    return NextResponse.json(exportPlan);
  } catch (error) {
    console.error('Export plan error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to create export plan' },
      { status: 500 }
    );
  }
}