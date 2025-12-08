export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createTestAwareClient, getTestAwareAuth } from "@/lib/auth/testHelpers";
import { createServiceRoleClient } from "@/lib/supabase/clients";
import { ensureWorkspaceForUser } from "@/lib/workspaces/ensureWorkspaceForUser";
import { apiFetch } from "@/lib/server/http";
import { z } from "zod";

interface RouteContext { params: Promise<{ id: string }> }

/**
 * Canon-Pure Document Recomposition API
 * 
 * Direct artifact operations - NO governance required per YARNNN Canon v2.3
 * Updates existing documents with fresh substrate from memory
 */

const RecomposeRequestSchema = z.object({
  intent: z.string().optional(),
  window_days: z.number().min(1).max(365).default(30),
  pinned_ids: z.array(z.string().uuid()).optional()
});

export async function POST(req: NextRequest, ctx: RouteContext) {
  try {
    const { id: document_id } = await ctx.params;
    const raw = await req.json().catch(() => ({}));

    console.log('[Recompose API] Received raw request:', JSON.stringify(raw, null, 2));

    const parsed = RecomposeRequestSchema.safeParse(raw);

    if (!parsed.success) {
      console.error('[Recompose API] Validation failed:', JSON.stringify({
        raw,
        errors: parsed.error.flatten()
      }, null, 2));
      return NextResponse.json({
        error: "Invalid recompose request",
        details: parsed.error.flatten(),
        received: raw
      }, { status: 422 });
    }

    const { intent, window_days, pinned_ids } = parsed.data;
    const supabase = createTestAwareClient({ cookies });
    const serviceSupabase = createServiceRoleClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);

    // Get workspace (required for all operations)
    const workspace = isTest 
      ? { id: '00000000-0000-0000-0000-000000000002' }
      : await ensureWorkspaceForUser(userId, supabase);

    // Load and verify document access
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('id, basket_id, title, workspace_id, metadata')
      .eq('id', document_id)
      .eq('workspace_id', workspace.id)
      .single();
      
    if (docError || !document) {
      return NextResponse.json({ error: "Document not found or access denied" }, { status: 404 });
    }

    // Canon-Pure: Direct document update (artifact operation)
    const { error: updateError } = await serviceSupabase
      .from('documents')
      .update({
        metadata: {
          ...(document.metadata || {}),
          recomposition_intent: intent,
          recomposition_timestamp: new Date().toISOString(),
          composition_status: 'processing', // Set status for frontend polling
          window_days,
          pinned_ids: pinned_ids || [],
        },
        updated_at: new Date().toISOString(),
      })
      .eq('id', document_id);

    if (updateError) {
      return NextResponse.json({ 
        error: "Failed to update document for recomposition", 
        details: updateError.message 
      }, { status: 500 });
    }

    // Trigger P4 recomposition asynchronously (direct agent call, not governance)
    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
      const p4Url = `${apiBaseUrl}/api/agents/p4-composition`;

      console.log('[Recompose API] Triggering P4 composition:', {
        url: p4Url,
        document_id,
        basket_id: document.basket_id,
        workspace_id: workspace.id,
        operation_type: 'recompose'
      });

      const recompositionResponse = await fetch(p4Url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`
        },
        body: JSON.stringify({
          document_id,
          basket_id: document.basket_id,
          workspace_id: workspace.id,
          intent: intent || 'Recompose with latest memory',
          window: { days: window_days },
          pinned_ids: pinned_ids || [],
          operation_type: 'recompose'
        })
      });

      if (!recompositionResponse.ok) {
        const errorText = await recompositionResponse.text().catch(() => 'Unable to read error');
        console.warn('[Recompose API] P4 composition trigger failed:', {
          status: recompositionResponse.status,
          statusText: recompositionResponse.statusText,
          error: errorText
        });
      } else {
        const result = await recompositionResponse.json().catch(() => ({}));
        console.log('[Recompose API] P4 composition triggered successfully:', result);
      }
    } catch (e) {
      console.error('[Recompose API] P4 composition async trigger exception:', e);
      // Don't fail the request - document was updated successfully
    }

    return NextResponse.json({
      success: true,
      document_id,
      title: document.title,
      status: 'recomposing',
      recomposition_started: true,
      message: 'Document recomposition started'
    }, { status: 200 });

  } catch (error) {
    console.error('Document recomposition error:', error);
    return NextResponse.json({ 
      error: "Document recomposition failed", 
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}
