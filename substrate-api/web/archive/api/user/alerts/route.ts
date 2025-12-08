export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';

/**
 * Clean User Alerts API
 * 
 * Canon v3.0: Real-time actionable alerts (service layer)
 * Shows things requiring user attention or awareness
 * NOT historical knowledge story
 */

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const limit = Math.min(parseInt(url.searchParams.get('limit') || '20'), 50);
    const onlyActionable = url.searchParams.get('actionable') === 'true';
    const severity = url.searchParams.get('severity') as 'info' | 'warning' | 'error' | 'critical' | null;
    
    const supabase = createServerSupabaseClient() as any;
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Build query for active alerts
    let query = supabase
      .from('user_alerts')
      .select(`
        id,
        alert_type,
        severity,
        title,
        message,
        actionable,
        action_url,
        action_label,
        related_entities,
        expires_at,
        created_at,
        read_at
      `)
      .eq('user_id', userId)
      .eq('workspace_id', workspace.id)
      .is('dismissed_at', null) // Only active alerts
      .order('created_at', { ascending: false })
      .limit(limit);

    // Filter by actionable if requested
    if (onlyActionable) {
      query = query.eq('actionable', true);
    }

    // Filter by severity if requested
    if (severity) {
      query = query.eq('severity', severity);
    }

    const { data: alerts, error } = await query;

    if (error) {
      console.error('User alerts query error:', error);
      // Graceful handling for missing table during migration
      if (error.code === '42P01') {
        return NextResponse.json({
          success: true,
          alerts: [],
          counts: { total: 0, unread: 0, actionable: 0 },
          workspace_id: workspace.id
        });
      }
      return NextResponse.json({ error: "Failed to load alerts" }, { status: 500 });
    }

    // Get counts for badge
    const { data: counts, error: countError } = await supabase
      .from('user_alerts')
      .select('id, actionable, read_at')
      .eq('user_id', userId)
      .eq('workspace_id', workspace.id)
      .is('dismissed_at', null);

    const badgeCounts = {
      total: counts?.length || 0,
      unread: counts?.filter((a: any) => !a.read_at).length || 0,
      actionable: counts?.filter((a: any) => a.actionable && !a.read_at).length || 0
    };

    // Handle missing table for count query too
    if (countError && countError.code === '42P01') {
      badgeCounts.total = 0;
      badgeCounts.unread = 0;
      badgeCounts.actionable = 0;
    }

    // Transform for frontend
    const alertList = (alerts || []).map((alert: any) => ({
      id: alert.id,
      type: alert.alert_type,
      severity: alert.severity,
      title: alert.title,
      message: alert.message,
      actionable: alert.actionable,
      actionUrl: alert.action_url,
      actionLabel: alert.action_label,
      relatedEntities: alert.related_entities || {},
      expiresAt: alert.expires_at,
      timestamp: alert.created_at,
      isRead: !!alert.read_at,
      // UI helpers
      icon: getAlertIcon(alert.alert_type, alert.severity),
      color: getSeverityColor(alert.severity)
    }));

    return NextResponse.json({
      success: true,
      alerts: alertList,
      counts: badgeCounts,
      workspace_id: workspace.id
    });

  } catch (error) {
    console.error('User alerts error:', error);
    return NextResponse.json({ 
      error: "Alerts fetch failed", 
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 });
  }
}

export async function PATCH(req: NextRequest) {
  try {
    const { alertId, action } = await req.json();
    
    if (!alertId || !action) {
      return NextResponse.json({ error: "alertId and action required" }, { status: 400 });
    }

    const supabase = createServerSupabaseClient() as any;
    const { userId } = await getAuthenticatedUser(supabase);

    let result;
    switch (action) {
      case 'markRead':
        result = await supabase.rpc('mark_alert_read', { p_alert_id: alertId });
        break;
      case 'dismiss':
        result = await supabase.rpc('dismiss_user_alert', { p_alert_id: alertId });
        break;
      default:
        return NextResponse.json({ error: "Invalid action" }, { status: 400 });
    }

    if (result.error) {
      return NextResponse.json({ error: "Action failed" }, { status: 500 });
    }

    return NextResponse.json({ success: true });

  } catch (error) {
    console.error('Alert action error:', error);
    return NextResponse.json({ 
      error: "Action failed", 
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 });
  }
}

// Helper functions for UI display
function getAlertIcon(alertType: string, severity: string): string {
  const typeIcons: Record<string, string> = {
    'approval.required': '👀',
    'decision.needed': '❓',
    'error.attention': '⚠️',
    'processing.completed': '✅',
    'document.ready': '📄',
    'insights.available': '💡',
    'governance.updated': '⚙️',
    'collaboration.update': '👥',
    'system.maintenance': '🔧',
    'system.performance': '⏱️',
    'system.security': '🔒',
    'system.storage': '💾'
  };
  
  const severityIcons: Record<string, string> = {
    'critical': '🚨',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️'
  };

  return typeIcons[alertType] || severityIcons[severity] || '📌';
}

function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    'info': 'text-blue-600',
    'warning': 'text-yellow-600',
    'error': 'text-red-600',
    'critical': 'text-red-800'
  };
  return colors[severity] || 'text-gray-600';
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}