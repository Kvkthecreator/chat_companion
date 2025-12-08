import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';

export async function GET(req: NextRequest) {
  try {
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);

    const searchParams = req.nextUrl.searchParams;
    const documentId = searchParams.get('document_id');
    const versionHash = searchParams.get('version_hash');
    const insightType = searchParams.get('insight_type') || 'doc_insight';

    if (!documentId) {
      return NextResponse.json({ error: 'document_id required' }, { status: 400 });
    }

    // Get document to verify access
    const { data: doc, error: docError } = await supabase
      .from('documents')
      .select('id, basket_id, workspace_id, current_version_hash')
      .eq('id', documentId)
      .maybeSingle();

    if (docError || !doc) {
      return NextResponse.json({ error: 'Document not found' }, { status: 404 });
    }

    // Search for insights derived from this document version
    // The derived_from JSONB field contains: [{"document_id": "...", "version_hash": "..."}]
    const targetVersionHash = versionHash || doc.current_version_hash;

    const { data: insights, error: insightsError } = await supabase
      .from('reflections_artifact')
      .select('*')
      .eq('basket_id', doc.basket_id)
      .eq('insight_type', insightType)
      .order('computation_timestamp', { ascending: false });

    if (insightsError) {
      console.error('Error fetching insights:', insightsError);
      return NextResponse.json({ error: 'Failed to fetch insights' }, { status: 500 });
    }

    // Filter in-memory for derived_from matching the document version
    // derived_from format: [{"document_id": "uuid", "version_hash": "doc_v..."}]
    const matchingInsight = insights?.find((insight) => {
      const derivedFrom = insight.derived_from || [];
      return derivedFrom.some(
        (ref: any) =>
          ref.document_id === documentId &&
          ref.version_hash === targetVersionHash
      );
    });

    if (matchingInsight) {
      return NextResponse.json({ insight: matchingInsight }, { status: 200 });
    }

    return NextResponse.json({ insight: null }, { status: 200 });
  } catch (e) {
    console.error('Reflections search error:', e);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
