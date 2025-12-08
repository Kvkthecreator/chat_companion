import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

export async function POST(
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

    const { eventId } = await request.json();

    if (!eventId) {
      return NextResponse.json(
        { error: "Event ID is required" },
        { status: 400 }
      );
    }

    // For now, just log the review - this could be expanded to track engagement metrics
    console.log(`User reviewed intelligence event ${eventId} for basket ${basketId}`);

    // You could store this in a separate table for analytics:
    // await supabase.from('intelligence_reviews').insert({
    //   event_id: eventId,
    //   basket_id: basketId,
    //   user_id: user.id,
    //   reviewed_at: new Date().toISOString()
    // });

    return NextResponse.json({ success: true });

  } catch (error) {
    console.error("Mark reviewed API error:", error);
    return NextResponse.json(
      { 
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}