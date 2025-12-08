import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

// POST create test basket
export async function POST(request: NextRequest) {
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

    // Create test basket
    const { data: basket, error: createError } = await supabase
      .from("baskets")
      .insert({
        name: "Debug Test Basket",
        title: "Debug Test Basket",
        description: "Test basket created for debugging",
        status: "INIT",
        workspace_id: workspace.id,
        metadata: {
          createdBy: user.id,
          source: "debug_endpoint",
          tags: ["test", "debug"]
        }
      })
      .select()
      .single();

    if (createError || !basket) {
      console.error("❌ Test basket creation error:", createError);
      return NextResponse.json(
        { error: "Failed to create test basket", details: createError?.message },
        { status: 500 }
      );
    }

    console.log("✅ Test basket created:", basket.id);

    const response = NextResponse.json({
      success: true,
      basket,
      message: `Test basket created with ID: ${basket.id}`
    });
    
    response.headers.set('Access-Control-Allow-Origin', '*');
    response.headers.set('Access-Control-Allow-Methods', 'POST, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    return response;

  } catch (error) {
    console.error("❌ Create test basket error:", error);
    return NextResponse.json(
      { 
        error: "Failed to create test basket",
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
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      'Access-Control-Max-Age': '86400',
    },
  });
}