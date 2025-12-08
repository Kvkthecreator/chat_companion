import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { withSchema } from '@/lib/api/withSchema';
import { 
  GetDocumentsResponseSchema, 
  CreateDocumentRequestSchema, 
  CreateDocumentResponseSchema,
  type DocumentDTO,
  type CreateDocumentRequest 
} from '@/shared/contracts/documents';
import { apiUrl } from '@/lib/env';

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(req: NextRequest, ctx: RouteContext) {
  const { id } = await ctx.params;
  
  // Authentication and workspace validation
  const supabase = createServerSupabaseClient();
  const { userId } = await getAuthenticatedUser(supabase);
  const workspace = await ensureWorkspaceForUser(userId, supabase);

  // Validate basket belongs to workspace
  const { data: basket, error: basketError } = await supabase
    .from('baskets')
    .select('id, workspace_id')
    .eq('id', id)
    .eq('workspace_id', workspace.id)
    .maybeSingle();

  if (basketError || !basket) {
    return NextResponse.json({ error: 'basket not found' }, { status: 404 });
  }

  // Query document heads (one row per artifact)
  const { data, error } = await supabase
    .from('documents')
    .select('id, basket_id, title, doc_type, current_version_hash, updated_at, metadata')
    .eq('basket_id', id)
    .order('updated_at', { ascending: false });

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 400 });
  }

  // Transform to DocumentDTO format
  const documents: DocumentDTO[] = (data || []).map((doc: any) => ({
    id: doc.id,
    basket_id: doc.basket_id,
    title: doc.title,
    doc_type: doc.doc_type || 'artifact_other',
    current_version_hash: doc.current_version_hash,
    latest_version_created_at: doc.updated_at,
    updated_at: doc.updated_at,
    metadata: doc.metadata || {},
  }));

  return withSchema(GetDocumentsResponseSchema, {
    documents,
    last_cursor: documents.length > 0 ? documents[documents.length - 1].updated_at : undefined,
  }, { status: 200 });
}

// POST /api/baskets/[id]/documents - Create document in basket
export async function POST(request: NextRequest, ctx: RouteContext) {
  try {
    const { id: basketId } = await ctx.params;
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    // Parse and validate request body
    const body = await request.json();
    const parseResult = CreateDocumentRequestSchema.safeParse({
      ...body,
      basket_id: basketId, // Auto-inject basket_id from URL
    });
    
    if (!parseResult.success) {
      return NextResponse.json(
        { error: 'Invalid request body', details: parseResult.error.flatten() },
        { status: 422 }
      );
    }

    const { basket_id, intent, template_id, target_audience, tone, pinned_ids, window_days, title } = parseResult.data as CreateDocumentRequest;
    const derivedTitle = typeof body?.title === 'string' && body.title.trim().length > 0
      ? body.title.trim()
      : title || 'Untitled Document';
    const compositionIntent = intent || 'Compose document from latest memory';

    // Validate basket belongs to workspace
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basket_id)
      .eq('workspace_id', workspace.id)
      .maybeSingle();

    if (basketError || !basket) {
      return NextResponse.json({ error: 'basket not found' }, { status: 404 });
    }

    const authHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const bearer = request.headers.get('authorization');
    const sbToken = request.headers.get('sb-access-token');
    if (bearer) authHeaders['Authorization'] = bearer;
    if (sbToken) authHeaders['sb-access-token'] = sbToken;

    const composeUrl = new URL('/api/documents/compose', request.url);
    const res = await fetch(composeUrl.toString(), {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        basket_id,
        title: derivedTitle,
        intent: compositionIntent,
        template_id,
        target_audience,
        tone,
        pinned_ids,
        window_days,
      }),
    });

    const doc = await res.json();
    if (!res.ok || !doc?.document_id) {
      return NextResponse.json({ error: doc?.error || 'Failed to compose document' }, { status: res.status });
    }

    return withSchema(CreateDocumentResponseSchema, { document_id: doc.document_id }, { status: 201 });

  } catch (error) {
    console.error('Document creation error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
