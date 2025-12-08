/**
 * LEGACY P4 Presentation Endpoint - Deprecated
 * 
 * Use /api/presentation/compose for canonical P4 implementation
 * This endpoint maintained for backward compatibility only
 */

import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";
import { DocumentComposer } from "@/lib/presentation/DocumentComposer";

// Ensure this route is treated as dynamic (requires authentication)
export const dynamic = 'force-dynamic';

export async function POST(req: Request) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    // Get authenticated user
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Ensure user has workspace access
    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) {
      return NextResponse.json({ error: "Workspace access required" }, { status: 401 });
    }

    const body = await req.json().catch(() => ({}));
    const basketId = body?.basket_id;
    
    if (!basketId) {
      return NextResponse.json({ error: "basket_id required" }, { status: 400 });
    }

    const title = body?.title || `Narrative — ${new Date().toISOString().slice(0,10)}`;
    
    // Create pure narrative using canonical P4 implementation
    const narrativeContent = body?.content || `# ${title}

**Pattern:** Analyzing recent memory patterns...
**Tension:** Identifying areas of focus...  
**Question:** What are the next steps?

(Generated from basket: ${basketId})
`;

    // Use canonical P4 composition (pure narrative, no substrate references)
    const result = await DocumentComposer.createNarrative(
      title,
      [{
        id: 'main',
        content: narrativeContent,
        order: 1,
        title: title
      }],
      workspace.id,
      user.id,
      basketId,
      supabase
    );

    if (!result.success) {
      return NextResponse.json({ 
        error: result.error || "Failed to create narrative" 
      }, { status: 500 });
    }

    return NextResponse.json({ 
      docId: result.document?.id,
      title,
      composition_type: 'pure_narrative',
      pipeline: 'P4_PRESENTATION'
    });

  } catch (error) {
    console.error('Legacy narrative creation error:', error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}