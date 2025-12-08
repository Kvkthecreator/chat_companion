import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

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
        { error: "Failed to get or create workspace" },
        { status: 500 }
      );
    }

    // Parse request body
    const body = await request.json();
    const {
      name = "Untitled Basket",
      description = "",
      status = "active",
      tags = [],
    } = body ?? {};

    // Create basket in database
    const { data: basket, error: createError } = await supabase
      .from("baskets")
      .insert({
        name,
        status,
        workspace_id: workspace.id,
        tags,
        origin_template: description || null // Store description in origin_template if provided
      })
      .select()
      .single();

    if (createError || !basket) {
      console.error("Basket creation error:", createError);
      return NextResponse.json(
        { error: "Failed to create basket" },
        { status: 500 }
      );
    }

    return NextResponse.json(
      { 
        id: basket.id,
        name: basket.name,
        description: basket.origin_template || "", // Map origin_template back to description for API compatibility
        status: basket.status,
        created_at: basket.created_at,
      },
      { status: 201 }
    );

  } catch (error) {
    console.error("Basket API error:", error);
    return NextResponse.json(
      { 
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}

// Handle GET requests for listing baskets
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

    // Get baskets for the workspace
    const { data: baskets, error: fetchError } = await supabase
      .from("baskets")
      .select("id, name, status, created_at, origin_template")
      .eq("workspace_id", workspace.id)
      .order("created_at", { ascending: false });

    if (fetchError) {
      console.error("Baskets fetch error:", fetchError);
      return NextResponse.json(
        { error: "Failed to fetch baskets" },
        { status: 500 }
      );
    }

    // Map origin_template to description for API compatibility
    const mappedBaskets = (baskets || []).map((basket) => {
      const { origin_template, ...rest } = basket ?? {};
      return {
        ...rest,
        description: origin_template || "",
      };
    });

    return NextResponse.json(mappedBaskets);

  } catch (error) {
    console.error("Baskets GET API error:", error);
    return NextResponse.json(
      { 
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}
