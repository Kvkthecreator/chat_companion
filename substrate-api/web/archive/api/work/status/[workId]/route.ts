export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createTestAwareClient, getTestAwareAuth } from '@/lib/auth/testHelpers';

/**
 * Work Status API - Universal Work Orchestration
 * Canon v2.1 compliant work status tracking
 */

export async function GET(req: NextRequest, { params }: { params: { workId: string } }) {
  try {
    const work_id = params?.workId;
    if (!work_id) {
      return NextResponse.json({ error: 'Work ID required' }, { status: 400 });
    }

    const supabase = createTestAwareClient({ cookies });
    const { userId, isTest } = await getTestAwareAuth(supabase);

    const { data: workData, error: workError } = await supabase
      .from('agent_processing_queue')
      .select(`
        id, work_id, work_type, processing_state, processing_stage,
        work_payload, work_result, created_at, claimed_at, completed_at,
        error_message, user_id, workspace_id, basket_id, attempts
      `)
      .eq('work_id', work_id)
      .single();

    if (workError || !workData) {
      return NextResponse.json({ error: 'Work not found', details: workError?.message }, { status: 404 });
    }

    if (!isTest && workData.user_id !== userId) {
      return NextResponse.json({ error: 'Access denied' }, { status: 403 });
    }

    const progress = calculateProgress(workData.work_type, workData.processing_stage, workData.processing_state);
    const substrateImpact = await getSubstrateImpact(workData, supabase);

    const statusResponse = {
      work_id,
      work_type: workData.work_type,
      status: workData.processing_state,
      processing_stage: workData.processing_stage,
      progress_percentage: progress,
      basket_id: workData.basket_id,
      workspace_id: workData.workspace_id,
      user_id: workData.user_id,
      started_at: workData.claimed_at || workData.created_at,
      last_activity: workData.completed_at || workData.claimed_at || workData.created_at,
      estimated_completion: getEstimatedCompletion(workData),
      substrate_impact: substrateImpact,
      cascade_flow: {},
      error: workData.error_message
        ? { message: workData.error_message, attempts: workData.attempts }
        : undefined,
    };

    return NextResponse.json(statusResponse);
  } catch (error) {
    console.error('Work status API error:', error);
    return NextResponse.json(
      { error: 'Failed to get work status', details: error instanceof Error ? error.message : String(error) },
      { status: 500 },
    );
  }
}

function calculateProgress(workType: string, stage: string, state: string): number {
  if (state === 'completed') return 100;
  if (state === 'failed') return 0;
  if (state === 'pending') return 0;
  if (workType === 'P4_COMPOSE') {
    const stageProgress: Record<string, number> = {
      intent_analysis: 25,
      substrate_query: 50,
      substrate_selection: 75,
      document_composition: 90,
      processing: 10,
    };
    return stageProgress[stage] || 10;
  }
  if (state === 'processing') return 50;
  if (state === 'claimed') return 10;
  return 0;
}

async function getSubstrateImpact(workData: any, supabase: any): Promise<any> {
  if (workData.work_type !== 'P4_COMPOSE') return {};
  const workResult = workData.work_result || {};
  if (workData.processing_state === 'completed' && workResult.document_id) {
    try {
      const { data: refs } = await supabase
        .from('substrate_references')
        .select('substrate_type')
        .eq('document_id', workResult.document_id);
      const substrateCount = refs?.length || workResult.substrate_count || 0;
      const substrateTypes = refs ? [...new Set(refs.map((r: any) => r.substrate_type))].join(', ') : 'unknown';
      return {
        substrate_count: substrateCount,
        substrate_types: substrateTypes,
        summary: workResult.summary || `Composed with ${substrateCount} substrate items`,
        confidence: workResult.confidence || 0.8,
      };
    } catch (e) {
      console.warn('Failed to get substrate impact:', e);
    }
  }
  return {
    substrate_count: workResult.substrate_count || 0,
    summary: workResult.summary || 'Processing...',
    confidence: workResult.confidence || 0.0,
  };
}

function getEstimatedCompletion(workData: any): string | undefined {
  if (workData.processing_state === 'completed' || workData.processing_state === 'failed') return undefined;
  const estimateMinutes: Record<string, number> = { P4_COMPOSE: 2, P1_SUBSTRATE: 1, P2_GRAPH: 1, P3_REFLECTION: 1 };
  const minutes = estimateMinutes[workData.work_type] || 1;
  const startTime = new Date(workData.claimed_at || workData.created_at);
  const estimatedEnd = new Date(startTime.getTime() + minutes * 60 * 1000);
  return estimatedEnd.toISOString();
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}

