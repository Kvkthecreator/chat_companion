import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createTestAwareClient, getTestAwareAuth } from "@/lib/auth/testHelpers";
import { ensureWorkspaceForUser } from "@/lib/workspaces/ensureWorkspaceForUser";
import { getWorkspaceFlags, isValidatorRequired as isValidatorRequiredLegacy } from "@/lib/governance/flagsServer";

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(
  req: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id: basketId } = await ctx.params;
    const searchParams = new URL(req.url).searchParams;
    const status = searchParams.get('status');
    const kind = searchParams.get('kind');
    
    const supabase = createTestAwareClient({ cookies });
    const { userId, isTest } = await getTestAwareAuth(supabase);
    
    let workspace;
    try {
      workspace = isTest
        ? { id: '00000000-0000-0000-0000-000000000002' }
        : await ensureWorkspaceForUser(userId, supabase);
    } catch (workspaceError) {
      console.error('Workspace resolution failed:', workspaceError);
      return NextResponse.json({ 
        error: "Workspace access denied", 
        details: workspaceError instanceof Error ? workspaceError.message : String(workspaceError)
      }, { status: 403 });
    }
    
    let query = supabase
      .from('proposals')
      .select('*')
      .eq('basket_id', basketId)
      .order('created_at', { ascending: false });

    if (status) {
      query = query.eq('status', status);
    }
    if (kind) {
      query = query.eq('proposal_kind', kind);
    }

    const { data: proposals, error } = await query;

    if (error) {
      console.error('Database query failed:', error);
      return NextResponse.json({ 
        error: "Failed to fetch proposals", 
        details: error.message 
      }, { status: 500 });
    }

    // Transform proposals to match canon contract format
    const items = proposals?.map((proposal: any) => {
      const ops = Array.isArray(proposal.ops) ? proposal.ops : [];
      const validator_report = normalizeValidatorReport(proposal.validator_report);
      const status = proposal.status || 'PROPOSED';
      const review_notes = proposal.review_notes || '';
      const auto_approved = (status === 'APPROVED' && proposal.is_executed === true) && 
                         typeof review_notes === 'string' && review_notes.toLowerCase().includes('auto-approved');
      return {
        id: proposal.id,
        proposal_kind: proposal.proposal_kind,
        origin: proposal.origin,
        source_host: proposal.source_host || proposal.metadata?.source_host,
        source_session: proposal.source_session || proposal.metadata?.source_session,
        status,
        ops_summary: validator_report.ops_summary || validator_report.impact_summary || generateOpsSummary(ops),
        confidence: typeof validator_report.confidence === 'number' ? validator_report.confidence : 0.5,
        impact_summary: validator_report.impact_summary || 'Impact unknown',
        created_at: proposal.created_at,
        validator_report,
        provenance: Array.isArray(proposal.provenance) ? proposal.provenance : [],
        ops,
        blast_radius: proposal.blast_radius || 'Local',
        auto_approved,
        reviewed_at: proposal.reviewed_at || null,
        executed_at: proposal.executed_at || null,
        review_notes,
        is_executed: proposal.is_executed === true || status === 'EXECUTED'
      };
    }) || [];

    return NextResponse.json({ items });

  } catch (error) {
    console.error('Proposals fetch error:', error);
    return NextResponse.json({ 
      error: "Internal server error", 
      details: error instanceof Error ? error.message : String(error),
      stack: process.env.NODE_ENV === 'development' ? (error instanceof Error ? error.stack : undefined) : undefined
    }, { status: 500 });
  }
}

export async function POST(
  req: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id: basketId } = await ctx.params;
    const { 
      proposal_kind, 
      ops, 
      origin = 'human',
      provenance = [],
      basis_snapshot_id 
    } = await req.json();
    
    const supabase = createTestAwareClient({ cookies });
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest
      ? { id: '00000000-0000-0000-0000-000000000002' }
      : await ensureWorkspaceForUser(userId, supabase);

    // Get workspace governance flags
    const workspaceFlags = await getWorkspaceFlags(supabase, workspace.id);
    
    // Feature flag check
    if (!workspaceFlags.governance_enabled) {
      return NextResponse.json({ 
        error: "Governance not enabled for this workspace",
        governance_status: "disabled" 
      }, { status: 503 });
    }

    // MANDATORY: Agent validation required per Governance Sacred Principle #3
    let validator_report;
    
    if (workspaceFlags.validator_required) {
      try {
        // Call P1 Validator Agent for mandatory validation
        const validationResponse = await fetch(`${process.env.AGENT_API_URL}/api/validator/validate-proposal`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            proposal_kind,
            operations: ops,
            basket_id: basketId,
            workspace_id: workspace.id
          })
        });

        if (!validationResponse.ok) {
          throw new Error(`Validator API error: ${validationResponse.status}`);
        }

        validator_report = await validationResponse.json();
        
        // Enforce minimum validation requirements
        if (!validator_report.confidence || !validator_report.impact_summary) {
          throw new Error('Invalid validator response - missing required fields');
        }

      } catch (validatorError) {
        // Validation failure blocks proposal creation
        return NextResponse.json({ 
          error: "Agent validation required but failed",
          details: validatorError instanceof Error ? validatorError.message : String(validatorError)
        }, { status: 503 });
      }
    } else {
      // Fallback validation when validator not required (development/testing)
      validator_report = {
        confidence: 0.7,
        dupes: [],
        ontology_hits: [],
        suggested_merges: [],
        warnings: ["Validation bypassed - validator not required by feature flags"],
        impact_summary: "Manual proposal - validation bypassed"
      };
    }
    
    // Get workspace_id for the basket
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('workspace_id')
      .eq('id', basketId)
      .single();

    if (basketError || !basket) {
      return NextResponse.json({ error: "Basket not found" }, { status: 404 });
    }

    // Create proposal
    const { data: proposal, error: createError } = await supabase
      .from('proposals')
      .insert({
        basket_id: basketId,
        workspace_id: basket.workspace_id,
        proposal_kind,
        ops,
        origin,
        provenance,
        basis_snapshot_id,
        validator_report,
        created_by: userId,
        status: 'PROPOSED'
      })
      .select()
      .single();

    if (createError) {
      return NextResponse.json({ error: "Failed to create proposal" }, { status: 500 });
    }

    // Emit governance timeline event
    const { error: timelineError } = await supabase.rpc('emit_timeline_event', {
      p_basket_id: basketId,
      p_event_type: 'proposal.submitted',
      p_event_data: {
        proposal_id: proposal.id,
        proposal_kind,
        origin
      },
      p_workspace_id: basket.workspace_id,
      p_actor_id: userId
    });

    if (timelineError) {
      console.error('Failed to emit timeline event:', timelineError);
    }

    return NextResponse.json({ 
      success: true,
      proposal_id: proposal.id,
      status: 'PROPOSED'
    });

  } catch (error) {
    console.error('Proposal creation error:', error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

function generateOpsSummary(ops: any[]): string {
  if (!Array.isArray(ops) || ops.length === 0) {
    return "No operations";
  }
  
  const opCounts = ops.reduce((acc, op) => {
    acc[op.type] = (acc[op.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  // Canon-compliant unified proposal summary: show blocks + context items
  const parts = [];
  if (opCounts.CreateBlock) {
    parts.push(`${opCounts.CreateBlock} block${opCounts.CreateBlock === 1 ? '' : 's'}`);
  }
  if (opCounts.CreateContextItem) {
    parts.push(`${opCounts.CreateContextItem} context item${opCounts.CreateContextItem === 1 ? '' : 's'}`);
  }
  
  // Add other operation types
  Object.entries(opCounts)
    .filter(([type]) => !['CreateBlock', 'CreateContextItem'].includes(type))
    .forEach(([type, count]) => {
      const displayName = type.replace(/([A-Z])/g, ' $1').toLowerCase().trim();
      parts.push(`${count} ${displayName}${count === 1 ? '' : 's'}`);
    });
  
  const summary = parts.join(', ');
  return parts.length > 1 ? `Unified proposal: ${summary}` : summary;
}

function normalizeValidatorReport(report: any) {
  const vr = report && typeof report === 'object' ? report : {};
  return {
    confidence: typeof vr.confidence === 'number' ? vr.confidence : 0.5,
    warnings: Array.isArray(vr.warnings) ? vr.warnings : [],
    impact_summary: typeof vr.impact_summary === 'string' ? vr.impact_summary : '',
    ops_summary: typeof vr.ops_summary === 'string' ? vr.ops_summary : '',
    dupes: Array.isArray(vr.dupes) ? vr.dupes : [],
    suggested_merges: Array.isArray(vr.suggested_merges) ? vr.suggested_merges : [],
    ontology_hits: Array.isArray(vr.ontology_hits) ? vr.ontology_hits : [],
  };
}
