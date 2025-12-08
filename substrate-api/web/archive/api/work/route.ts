export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createTestAwareClient, getTestAwareAuth } from "@/lib/auth/testHelpers";
import { createServiceRoleClient } from "@/lib/supabase/clients";
import { ensureWorkspaceForUser } from "@/lib/workspaces/ensureWorkspaceForUser";
import { z } from "zod";
import { routeWork } from "@/lib/governance/universalWorkRouter";
import { createTimelineEmitter } from "@/lib/canon/TimelineEventEmitter";

/**
 * Substrate Work Orchestration Endpoint
 * 
 * SUBSTRATE mutations flow through this endpoint for governance.
 * Artifact operations (documents, reflections) use direct REST APIs.
 * 
 * Canon v2.3 Compliance:
 * - Sacred Principle #1: Substrate-Only Governance
 * - Sacred Principle #2: User-Controlled Execution Mode  
 * - Sacred Principle #3: Confidence-Informed Routing (within governance)
 * - Sacred Principle #4: Artifact Independence
 */

const WorkRequestSchema = z.object({
  work_type: z.enum([
    'P0_CAPTURE',      // Raw dump capture (substrate - direct)
    'P1_SUBSTRATE',    // AI substrate creation (substrate - governed)
    'P2_GRAPH',        // Relationship mapping (substrate - governed)
    'MANUAL_EDIT',     // User substrate edits (substrate - governed)
    'PROPOSAL_REVIEW', // Manual proposal review (substrate - governed)
    'TIMELINE_RESTORE' // Historical restoration (substrate - governed)
    // P3_REFLECTION removed - now direct artifact operations via /api/reflections
    // P4_COMPOSE_NEW, P4_RECOMPOSE removed - now direct artifact operations via /api/documents
  ]),
  work_payload: z.object({
    operations: z.array(z.object({
      type: z.string(),
      data: z.record(z.any())
    })),
    basket_id: z.string().uuid(),
    confidence_score: z.number().min(0).max(1).optional(),
    user_override: z.enum(['require_review', 'allow_auto']).optional(),
    trace_id: z.string().optional(),
    provenance: z.array(z.string()).optional()
  }),
  priority: z.enum(['low', 'normal', 'high', 'urgent']).default('normal')
});

export async function POST(req: NextRequest) {
  try {
    const raw = await req.json().catch(() => null);
    const parsed = WorkRequestSchema.safeParse(raw);
    
    if (!parsed.success) {
      return NextResponse.json({ 
        error: "Invalid work request", 
        details: parsed.error.flatten() 
      }, { status: 422 });
    }

    const { work_type, work_payload, priority } = parsed.data;
    const supabase = createTestAwareClient({ cookies });
    const serviceSupabase = createServiceRoleClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);

    // Get workspace (required for all work)
    const workspace = isTest 
      ? { id: '00000000-0000-0000-0000-000000000002' }
      : await ensureWorkspaceForUser(userId, supabase);

    // Verify basket access for basket-scoped work
    if (work_payload.basket_id) {
      const { data: basket } = await supabase
        .from('baskets')
        .select('id')
        .eq('id', work_payload.basket_id)
        .eq('workspace_id', workspace.id)
        .single();
        
      if (!basket) {
        return NextResponse.json({ error: "Basket not found or access denied" }, { status: 404 });
      }
    }

    // Route through universal governance system
    // Use service role client for queue/proposals writes (bypass RLS),
    // after access is validated with user-scoped client above.
    const routingResult = await routeWork(serviceSupabase, {
      work_type,
      work_payload,
      workspace_id: workspace.id,
      user_id: userId,
      priority
    });

    // Emit timeline event for work initiation
    const timelineEmitter = createTimelineEmitter(serviceSupabase);
    await timelineEmitter.emitWorkInitiated({
      work_id: routingResult.work_id,
      work_type,
      workspace_id: workspace.id,
      user_id: userId,
      routing_decision: routingResult.routing_decision,
      basket_id: work_payload.basket_id
    });

    return NextResponse.json({
      success: true,
      work_id: routingResult.work_id,
      routing_decision: routingResult.routing_decision,
      execution_mode: routingResult.execution_mode,
      proposal_id: routingResult.proposal_id,
      status_url: `/api/work/status/${routingResult.work_id}`,
      message: getExecutionModeMessage(routingResult.execution_mode, routingResult.executed_immediately)
    }, { 
      status: routingResult.execution_mode === 'auto_execute' ? 201 : 202 
    });

  } catch (error) {
    console.error('Universal work orchestration error:', error);
    return NextResponse.json({ 
      error: "Work orchestration failed", 
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 });
  }
}

function getExecutionModeMessage(execution_mode: string, executed_immediately?: boolean): string {
  switch (execution_mode) {
    case 'auto_execute':
      return executed_immediately
        ? 'Work executed immediately based on governance policy'
        : 'Work queued for automatic execution based on governance policy';
    case 'create_proposal':
      return 'Proposal created for review based on governance policy';
    case 'confidence_routing':
      return 'Execution route determined by confidence within governance framework';
    default:
      return 'Work processed according to governance configuration';
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}
