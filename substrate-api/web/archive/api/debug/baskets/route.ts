import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

// GET debug baskets - Check what baskets exist
export async function GET(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Use getUser() for secure authentication
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

    // Ensure user has a workspace
    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) {
      return NextResponse.json(
        { error: "Failed to get workspace" },
        { status: 500 }
      );
    }

    console.log(`🔍 Debug: User ${user.id} in workspace ${workspace.id}`);

    // Get all baskets (not just user's workspace)
    const { data: allBaskets, error: allError } = await supabase
      .from("baskets")
      .select("id, name, title, status, workspace_id, created_at")
      .order("created_at", { ascending: false })
      .limit(20);

    // Get baskets in user's workspace
    const { data: userBaskets, error: userError } = await supabase
      .from("baskets")
      .select("id, name, title, status, workspace_id, created_at")
      .eq("workspace_id", workspace.id)
      .order("created_at", { ascending: false });

    const debugInfo = {
      user: {
        id: user.id,
        email: user.email
      },
      workspace: {
        id: workspace.id,
        name: workspace.name
      },
      allBaskets: allBaskets || [],
      userBaskets: userBaskets || [],
      basketCount: {
        total: allBaskets?.length || 0,
        userWorkspace: userBaskets?.length || 0
      },
      errors: {
        allBaskets: allError?.message,
        userBaskets: userError?.message
      }
    };

    console.log('🔍 Debug info:', debugInfo);

    const response = NextResponse.json(debugInfo);
    response.headers.set('Access-Control-Allow-Origin', '*');
    response.headers.set('Access-Control-Allow-Methods', 'GET, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    return response;

  } catch (error) {
    console.error("❌ Debug baskets error:", error);
    return NextResponse.json(
      { 
        error: "Debug failed",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}

// Handle preflight requests
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}