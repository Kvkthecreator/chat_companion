import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";
import { getPendingIntelligenceChanges } from "@/lib/intelligence/intelligenceEvents";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ basketId: string }> }
) {
  try {
    const { basketId } = await params;
    const supabase = createRouteHandlerClient({ cookies });
    
    // Authentication check
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    // Ensure workspace access
    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) {
      return NextResponse.json(
        { error: "Workspace access required" },
        { status: 403 }
      );
    }

    // Verify basket access
    const { data: basket, error: basketError } = await supabase
      .from("baskets")
      .select("id")
      .eq("id", basketId)
      .eq("workspace_id", workspace.id)
      .single();

    if (basketError || !basket) {
      return NextResponse.json(
        { error: "Basket not found" },
        { status: 404 }
      );
    }

    // Get pending intelligence changes
    const pendingEvents = await getPendingIntelligenceChanges(supabase, basketId);

    return NextResponse.json({
      events: pendingEvents,
      count: pendingEvents.length,
      hasUpdates: pendingEvents.length > 0
    });

  } catch (error) {
    console.error("Pending intelligence API error:", error);
    return NextResponse.json(
      { 
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}