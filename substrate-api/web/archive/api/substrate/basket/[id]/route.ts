import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createRouteHandlerClient } from '@/lib/supabase/clients';
import { ensureWorkspaceServer } from '@/lib/workspaces/ensureWorkspaceServer';
import { analyzeBasketIntelligence } from '@/lib/intelligence/sharedAnalysis';
import type { SubstrateIntelligence } from '@/lib/substrate/types';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: basketId } = await params;
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get authenticated user
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    // Ensure workspace access
    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) {
      return NextResponse.json({ error: 'Workspace access required' }, { status: 403 });
    }

    console.log(`[Substrate API] Analyzing basket ${basketId} for workspace ${workspace.id}`);
    
    // Use shared analysis instead of making HTTP requests - much faster!
    const intelligenceData = await analyzeBasketIntelligence(supabase, basketId, workspace.id);
    
    if (!intelligenceData) {
      console.error(`[Substrate API] Failed to analyze basket ${basketId} - returning 404`);
      return NextResponse.json({ error: 'Basket not found' }, { status: 404 });
    }
    
    console.log(`[Substrate API] Successfully analyzed basket ${basketId}`)

    // Get basket data separately for transformation
    const { data: basketData } = await supabase
      .from('baskets')
      .select('*')
      .eq('id', basketId)
      .eq('workspace_id', workspace.id)
      .single();
      
    const { data: rawDumps } = await supabase
      .from('raw_dumps')
      .select('id, body_md, created_at')
      .eq('basket_id', basketId)
      .eq('workspace_id', workspace.id);
    
    // Transform to substrate format  
    const substrateIntelligence = transformToSubstrateFormat(intelligenceData, rawDumps || []);

    return NextResponse.json(substrateIntelligence);

  } catch (error) {
    console.error('Substrate intelligence error:', error);
    return NextResponse.json(
      { error: 'Failed to generate substrate intelligence' },
      { status: 500 }
    );
  }
}

function transformToSubstrateFormat(intelligenceData: any, rawDumps: any[] = []): SubstrateIntelligence {
  // Transform shared analysis data to substrate format
  console.log(`[Substrate API] Transforming intelligence data:`, { 
    themes: intelligenceData.themes?.length, 
    confidence: intelligenceData.confidenceScore,
    rawDumps: rawDumps.length
  });
  
  return {
    basketInfo: {
      id: 'basket-id', // Placeholder - could be populated from intelligenceData if needed
      name: 'Workspace', // Placeholder - could be populated from intelligenceData if needed  
      status: 'active',
      lastUpdated: intelligenceData.lastUpdated,
      documentCount: intelligenceData.insights?.length || 0,
      workspaceId: 'workspace-id'
    },
    contextUnderstanding: {
      intent: intelligenceData.understanding || 'No understanding available',
      themes: intelligenceData.themes || [],
      coherenceScore: Math.max(0.1, (intelligenceData.confidenceScore || 0) / 100),
      lastAnalysis: intelligenceData.lastUpdated
    },
    documents: [], // Simplified - documents aren't needed for basic substrate display
    intelligence: {
      insights: intelligenceData.insights || [],
      recommendations: intelligenceData.recommendations || [],
      contextAlerts: rawDumps.map((dump: any) => ({
        id: dump.id,
        type: 'quality' as const,
        priority: 'medium',
        severity: 'info' as const,
        title: 'Context Added',
        description: (dump.body_md || '').substring(0, 200) + '...',
        timestamp: dump.created_at,
        affectedDocuments: [],
        suggestedActions: []
      })),
      recentActivity: []
    },
    substrateHealth: {
      contextQuality: Math.max(0.1, (intelligenceData.confidenceScore || 0) / 100),
      documentAlignment: calculateDocumentAlignment(intelligenceData),
      evolutionRate: calculateEvolutionRate(intelligenceData)
    }
  };
}

function calculateDocumentAlignment(intelligenceData: any): number {
  // Calculate alignment based on theme consistency and content quality
  const themes = intelligenceData.themes || [];
  const insights = intelligenceData.insights || [];
  const recommendations = intelligenceData.recommendations || [];
  
  if (themes.length === 0 && insights.length === 0) return 0.1;
  
  // Higher alignment when themes are consistent with insights/recommendations
  let alignmentScore = 0.1;
  
  // Theme consistency bonus
  if (themes.length > 0) {
    alignmentScore += 0.3;
    if (themes.length > 1) alignmentScore += 0.2; // Multiple themes show depth
  }
  
  // Content consistency bonus
  if (insights.length > 0) alignmentScore += 0.2;
  if (recommendations.length > 0) alignmentScore += 0.2;
  
  // Bonus for having both insights and recommendations
  if (insights.length > 0 && recommendations.length > 0) alignmentScore += 0.1;
  
  return Math.min(alignmentScore, 1.0);
}

function calculateEvolutionRate(intelligenceData: any): 'stable' | 'growing' | 'active' {
  const confidence = intelligenceData.confidenceScore || 0;
  const memoryGrowth = intelligenceData.memoryGrowth || 0;
  
  // Base on actual activity metrics
  if (memoryGrowth > 10 && confidence > 60) return 'active';
  if (memoryGrowth > 5 || confidence > 35) return 'growing';
  return 'stable';
}

// All analysis logic moved to shared utility - this file is now much simpler!