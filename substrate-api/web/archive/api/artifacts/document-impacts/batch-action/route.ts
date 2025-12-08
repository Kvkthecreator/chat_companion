import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

export async function POST(req: NextRequest) {
  try {
    const { impact_ids, action, workspace_id, notes = '' } = await req.json();
    
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
    if (!workspace || workspace.id !== workspace_id) {
      return NextResponse.json({ error: "Workspace access required" }, { status: 401 });
    }

    // Validate inputs
    if (!Array.isArray(impact_ids) || impact_ids.length === 0) {
      return NextResponse.json({ error: "Impact IDs array required" }, { status: 400 });
    }

    const validActions = ['approve_all', 'defer_all', 'skip_all'];
    if (!validActions.includes(action)) {
      return NextResponse.json({ error: "Invalid batch action" }, { status: 400 });
    }

    // Get all impacts to process
    const { data: impacts, error: impactsError } = await supabase
      .from('document_impacts')
      .select('*')
      .in('id', impact_ids)
      .eq('workspace_id', workspace_id);

    if (impactsError) {
      return NextResponse.json({ error: "Failed to fetch impacts" }, { status: 500 });
    }

    if (!impacts || impacts.length === 0) {
      return NextResponse.json({ error: "No impacts found" }, { status: 404 });
    }

    // Map batch action to individual status
    const statusMap = {
      'approve_all': 'user_approved',
      'defer_all': 'user_deferred',
      'skip_all': 'user_skipped'
    };

    const newStatus = statusMap[action as keyof typeof statusMap];
    const shouldResolve = action !== 'defer_all';

    const results = {
      processed: 0,
      failed: 0,
      errors: [] as string[]
    };

    // Process each impact
    for (const impact of impacts) {
      try {
        // Update impact status
        const { error: updateError } = await supabase
          .from('document_impacts')
          .update({
            status: newStatus,
            user_choice: {
              action: action.replace('_all', ''),
              timestamp: new Date().toISOString(),
              user_id: user.id,
              batch_action: true
            },
            user_notes: notes,
            resolved_by: shouldResolve ? user.id : null,
            resolved_at: shouldResolve ? new Date().toISOString() : null,
            updated_at: new Date().toISOString()
          })
          .eq('id', impact.id);

        if (updateError) {
          results.failed++;
          results.errors.push(`Impact ${impact.id}: ${updateError.message}`);
          continue;
        }

        // If approved, execute document update
        if (action === 'approve_all') {
          try {
            await executeDocumentUpdate(supabase, impact, user.id);
          } catch (executeError) {
            console.error(`Document update failed for impact ${impact.id}:`, executeError);
            
            // Mark as failed
            await supabase
              .from('document_impacts')
              .update({
                status: 'pending',
                user_notes: `${notes}\n\nBatch execution failed: ${executeError instanceof Error ? executeError.message : String(executeError)}`
              })
              .eq('id', impact.id);
              
            results.failed++;
            results.errors.push(`Impact ${impact.id}: Execution failed`);
            continue;
          }
        }

        results.processed++;

        // Update batch statistics if applicable
        if (impact.batch_id) {
          await supabase.rpc('update_batch_stats', { p_batch_id: impact.batch_id });
        }

      } catch (error) {
        results.failed++;
        results.errors.push(`Impact ${impact.id}: ${error instanceof Error ? error.message : String(error)}`);
      }
    }

    // Emit batch timeline event
    await supabase.rpc('emit_timeline_event', {
      p_basket_id: null, // Document impacts are workspace-level
      p_event_type: 'document_impacts.batch_processed',
      p_event_data: {
        action: action,
        processed_count: results.processed,
        failed_count: results.failed,
        impact_ids: impact_ids
      },
      p_workspace_id: workspace_id,
      p_actor_id: user.id
    });

    return NextResponse.json({
      success: true,
      action: action,
      results: results
    });

  } catch (error) {
    console.error('Batch document impact action error:', error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

/**
 * Execute document update (shared with individual action endpoint)
 */
async function executeDocumentUpdate(
  supabase: any,
  impact: any,
  userId: string
): Promise<void> {
  switch (impact.proposed_action_type) {
    case 'recompose':
      await executeRecomposition(supabase, impact, userId);
      break;
    case 'add_references':
      await executeAddReferences(supabase, impact, userId);
      break;
    case 'update_references':
      await executeUpdateReferences(supabase, impact, userId);
      break;
    case 'version_snapshot':
      await executeVersionSnapshot(supabase, impact, userId);
      break;
    default:
      throw new Error(`Unknown proposed action type: ${impact.proposed_action_type}`);
  }
}

async function executeRecomposition(supabase: any, impact: any, userId: string): Promise<void> {
  // Call P4 presentation pipeline to recompose document with updated substrate
  const { error } = await supabase.rpc('fn_p4_recompose_document', {
    p_document_id: impact.document_id,
    p_user_id: userId,
    p_reason: `Document recomposition after substrate changes (impact: ${impact.id})`
  });

  if (error) {
    throw new Error(`Document recomposition failed: ${error.message}`);
  }
}

async function executeAddReferences(supabase: any, impact: any, userId: string): Promise<void> {
  const references = impact.affected_references || [];
  
  for (const ref of references) {
    const { error } = await supabase
      .from('substrate_references')
      .insert({
        document_id: impact.document_id,
        substrate_id: ref.id,
        substrate_type: ref.type,
        role: ref.relationship_to_document || 'reference',
        weight: 0.5,
        added_by: userId,
        added_at: new Date().toISOString()
      });

    if (error && !error.message.includes('duplicate')) {
      console.error(`Failed to add reference ${ref.id}:`, error);
    }
  }
}

async function executeUpdateReferences(supabase: any, impact: any, userId: string): Promise<void> {
  const references = impact.affected_references || [];
  
  for (const ref of references) {
    const { error } = await supabase
      .from('substrate_references')
      .update({
        status: 'removed',
        updated_by: userId,
        updated_at: new Date().toISOString()
      })
      .eq('document_id', impact.document_id)
      .eq('substrate_id', ref.id);

    if (error) {
      console.error(`Failed to update reference ${ref.id}:`, error);
    }
  }
}

async function executeVersionSnapshot(supabase: any, impact: any, userId: string): Promise<void> {
  const { error } = await supabase.rpc('fn_create_document_version_snapshot', {
    p_document_id: impact.document_id,
    p_snapshot_reason: `Version snapshot before substrate changes (impact: ${impact.id})`,
    p_created_by: userId
  });

  if (error) {
    throw new Error(`Version snapshot creation failed: ${error.message}`);
  }

  await executeRecomposition(supabase, impact, userId);
}