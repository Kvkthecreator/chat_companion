import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";
import { analyzeBasketIntelligence } from "@/lib/intelligence/sharedAnalysis";

interface NextStep {
  description: string;
  priority: number;
}

interface Action {
  type: string;
  label: string;
  enabled: boolean;
  primary?: boolean;
}

interface BasketIntelligenceDashboard {
  understanding: string;
  themes: string[];
  nextSteps: NextStep[];
  actions: Action[];
  confidenceScore: number;
  memoryGrowth: number;
  lastUpdated: string;
}

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
      console.error("Authentication error:", authError);
      return NextResponse.json(
        { error: "Authentication required" },
        { status: 401 }
      );
    }

    // Ensure user has workspace access
    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) {
      console.error("Workspace access failed");
      return NextResponse.json(
        { error: "Workspace access required" },
        { status: 403 }
      );
    }

    // Use shared analysis for consistency and performance
    const intelligence = await analyzeBasketIntelligence(supabase, basketId, workspace.id);
    
    if (!intelligence) {
      console.error("Basket not found or analysis failed");
      return NextResponse.json(
        { error: "Basket not found or access denied" },
        { status: 404 }
      );
    }

    console.log(`[Dashboard API] Generated intelligence for basket ${basketId}: ${intelligence.themes.length} themes, confidence ${intelligence.confidenceScore}%`);

    return NextResponse.json(intelligence, {
      headers: {
        'Cache-Control': 'public, max-age=30, s-maxage=30',
        'Pragma': 'no-cache'
      }
    });

  } catch (error) {
    console.error("Dashboard API error:", error);
    return NextResponse.json(
      { 
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}

// All analysis logic moved to shared utility for better performance and consistency!