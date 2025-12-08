/**
 * Workspace Governance Settings API
 * 
 * Allows workspace admins to configure governance policies per workspace.
 * Supports per-entry-point policies and risk management settings.
 */

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";

// Ensure this route is treated as dynamic (requires authentication)
export const dynamic = 'force-dynamic';
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";

export async function GET(req: NextRequest) {
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

    // Get workspace governance settings (raw table read)
    const { data: settings, error } = await supabase
      .from('workspace_governance_settings')
      .select('*')
      .eq('workspace_id', workspace.id)
      .single();

    if (error && error.code !== 'PGRST116') { // Not found is OK
      return NextResponse.json({ 
        error: "Failed to fetch governance settings" 
      }, { status: 500 });
    }

    // Return settings or defaults (filtered to canon-safe fields)
    if (settings) {
      return NextResponse.json({
        workspace_id: workspace.id,
        settings: {
          governance_enabled: settings.governance_enabled,
          validator_required: settings.validator_required,
          direct_substrate_writes: false, // Canon: never exposed/true
          governance_ui_enabled: settings.governance_ui_enabled,
          retention_enabled: settings.retention_enabled,
          retention_policy: settings.retention_policy || {},
          
          entry_point_policies: {
            onboarding_dump: 'direct',
            manual_edit: settings.ep_manual_edit === 'direct' ? 'proposal' : settings.ep_manual_edit,
            graph_action: settings.ep_graph_action === 'direct' ? 'proposal' : settings.ep_graph_action,
            timeline_restore: 'proposal'
          },
          
          default_blast_radius: settings.default_blast_radius === 'Global' ? 'Scoped' : settings.default_blast_radius
        },
        created_at: settings.created_at,
        updated_at: settings.updated_at,
        source: 'workspace_database'
      });
    } else {
      // Return Canon-compliant defaults (matches database function)
      return NextResponse.json({
        workspace_id: workspace.id,
        settings: {
          governance_enabled: true,
          validator_required: false,
          direct_substrate_writes: false,
          governance_ui_enabled: true,
          retention_enabled: false,
          retention_policy: {},
          
          entry_point_policies: {
            onboarding_dump: 'direct',
            manual_edit: 'proposal',
            graph_action: 'proposal',
            timeline_restore: 'proposal'
          },
          
          default_blast_radius: 'Scoped'
        },
        source: 'canon_compliant_defaults',
        note: 'No workspace-specific settings found - using Canon-compliant defaults'
      });
    }

  } catch (error) {
    console.error('Governance settings fetch error:', error);
    return NextResponse.json({ 
      error: "Internal server error" 
    }, { status: 500 });
  }
}

export async function PUT(req: NextRequest) {
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

    // Check if user is workspace admin/owner
    const { data: membership, error: membershipError } = await supabase
      .from('workspace_memberships')
      .select('role')
      .eq('workspace_id', workspace.id)
      .eq('user_id', user.id)
      .single();

    if (membershipError || !membership || !['admin','owner'].includes(membership.role)) {
      return NextResponse.json({ 
        error: "Admin access required to modify governance settings" 
      }, { status: 403 });
    }

    const body = await req.json();
    const governance_enabled = Boolean(body.governance_enabled);
    const validator_required = Boolean(body.validator_required);
    const governance_ui_enabled = Boolean(body.governance_ui_enabled);
    const retention_enabled = Boolean(body.retention_enabled);
    const retention_policy = body.retention_policy && typeof body.retention_policy === 'object' ? body.retention_policy : {};
    const entry_point_policies = body.entry_point_policies || {};
    const default_blast_radius_in = body.default_blast_radius;

    // Validate entry point policies
    const validPolicies = ['proposal', 'direct', 'hybrid'];
    const validBlastRadius = ['Local', 'Scoped', 'Global'];
    
    if (entry_point_policies) {
      for (const [ep, policy] of Object.entries(entry_point_policies)) {
        if (!validPolicies.includes(policy as string)) {
          return NextResponse.json({
            error: `Invalid policy '${policy}' for entry point '${ep}'. Must be: ${validPolicies.join(', ')}`
          }, { status: 400 });
        }
      }
    }

    if (default_blast_radius_in && !validBlastRadius.includes(default_blast_radius_in)) {
      return NextResponse.json({
        error: `Invalid blast_radius '${default_blast_radius_in}'. Must be: ${validBlastRadius.join(', ')}`
      }, { status: 400 });
    }

    // Canon coercions
    const sanitized = {
      ep_onboarding_dump: 'direct', // P0 must be direct
      ep_manual_edit: entry_point_policies?.manual_edit === 'direct' ? 'proposal' : (entry_point_policies?.manual_edit || 'proposal'),
      ep_graph_action: entry_point_policies?.graph_action === 'direct' ? 'proposal' : (entry_point_policies?.graph_action || 'proposal'),
      ep_timeline_restore: 'proposal',
      // Artifacts removed: document_edit, reflection_suggestion
      default_blast_radius: validBlastRadius.includes(default_blast_radius_in) && default_blast_radius_in !== 'Global' ? default_blast_radius_in : 'Scoped'
    } as const;

    // Upsert workspace governance settings
    const { data: settings, error: upsertError } = await supabase
      .from('workspace_governance_settings')
      .upsert({
        workspace_id: workspace.id,
        governance_enabled: governance_enabled,
        validator_required: validator_required,
        direct_substrate_writes: false, // Canon: never allow direct substrate writes
        governance_ui_enabled: governance_ui_enabled,
        retention_enabled: retention_enabled,
        retention_policy: retention_policy,
        
        // Entry point policies (with defaults)
        ep_onboarding_dump: sanitized.ep_onboarding_dump,
        ep_manual_edit: sanitized.ep_manual_edit,
        ep_graph_action: sanitized.ep_graph_action,
        ep_timeline_restore: sanitized.ep_timeline_restore,
        
        default_blast_radius: sanitized.default_blast_radius
      }, {
        onConflict: 'workspace_id'
      })
      .select()
      .single();

    if (upsertError) {
      return NextResponse.json({ 
        error: "Failed to update governance settings",
        details: upsertError.message
      }, { status: 500 });
    }

    // Emit settings change event
    await supabase.rpc('emit_timeline_event', {
      p_basket_id: null, // Workspace-level event
      p_event_type: 'governance.settings_updated',
      p_event_data: {
        workspace_id: workspace.id,
        updated_by: user.id,
        new_settings: settings
      },
      p_workspace_id: workspace.id,
      p_actor_id: user.id
    });

    return NextResponse.json({
      success: true,
      workspace_id: workspace.id,
      settings: {
        governance_enabled: settings.governance_enabled,
        validator_required: settings.validator_required,
        direct_substrate_writes: false,
        governance_ui_enabled: settings.governance_ui_enabled,
        retention_enabled: settings.retention_enabled,
        retention_policy: settings.retention_policy || {},
        
        entry_point_policies: {
          onboarding_dump: 'direct',
          manual_edit: settings.ep_manual_edit,
          graph_action: settings.ep_graph_action,
          timeline_restore: settings.ep_timeline_restore
        },
        
        default_blast_radius: settings.default_blast_radius
      },
      updated_at: settings.updated_at
    });

  } catch (error) {
    console.error('Governance settings update error:', error);
    return NextResponse.json({ 
      error: "Internal server error" 
    }, { status: 500 });
  }
}
