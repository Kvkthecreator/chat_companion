import { NextRequest, NextResponse } from "next/server";
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getTestAwareAuth } from '@/lib/auth/testHelpers';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { withSchema } from '@/lib/api/withSchema';
import { 
  AttachSubstrateRequestSchema,
  AttachSubstrateResponseSchema,
  GetDocumentReferencesRequestSchema,
  GetDocumentReferencesResponseSchema,
  type AttachSubstrateRequest,
  type AttachSubstrateResponse,
  type GetDocumentReferencesRequest,
  type GetDocumentReferencesResponse,
  type SubstrateReferenceDTO
} from '@/shared/contracts/substrate_references';

interface RouteContext {
  params: Promise<{ id: string }>;
}

// GET /api/documents/[id]/references - List substrate references
export async function GET(
  request: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id } = await ctx.params;
    const url = new URL(request.url);
    const queryParams = Object.fromEntries(url.searchParams);

    // Parse query parameters
    const parseResult = GetDocumentReferencesRequestSchema.safeParse(queryParams);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: 'Invalid query parameters', details: parseResult.error.flatten() },
        { status: 422 }
      );
    }

    const { substrate_types, role, limit, cursor } = parseResult.data;
    const supabase = createServerSupabaseClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // Verify document access
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('id, workspace_id')
      .eq('id', id)
      .maybeSingle();

    if (docError || !document) {
      return NextResponse.json({ error: 'document not found' }, { status: 404 });
    }

    if (document.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'unauthorized' }, { status: 403 });
    }

    // Build query with filters
    let query = supabase
      .from('substrate_references')
      .select('*')
      .eq('document_id', id)
      .order('created_at', { ascending: false })
      .limit(limit);

    if (substrate_types && substrate_types.length > 0) {
      query = query.in('substrate_type', substrate_types);
    }

    if (role) {
      query = query.eq('role', role);
    }

    if (cursor) {
      // Use cursor-based pagination
      query = query.lt('created_at', cursor);
    }

    const { data: references, error: refError } = await query;

    if (refError) {
      console.error('Error fetching references:', refError);
      return NextResponse.json({ error: 'Failed to fetch references' }, { status: 500 });
    }

    const referenceDTOs: SubstrateReferenceDTO[] = (references || []).map(ref => ({
      id: ref.id,
      document_id: ref.document_id,
      substrate_type: ref.substrate_type,
      substrate_id: ref.substrate_id,
      role: ref.role,
      weight: ref.weight,
      snippets: ref.snippets || [],
      metadata: ref.metadata || {},
      created_at: ref.created_at,
      created_by: ref.created_by
    }));

    const response: GetDocumentReferencesResponse = {
      references: referenceDTOs,
      has_more: referenceDTOs.length === limit,
      next_cursor: referenceDTOs.length > 0 ? referenceDTOs[referenceDTOs.length - 1].created_at : undefined
    };

    return withSchema(GetDocumentReferencesResponseSchema, response, { status: 200 });

  } catch (error) {
    console.error('References fetch error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

// POST /api/documents/[id]/references - Attach substrate to document
export async function POST(
  request: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id } = await ctx.params;
    const body = await request.json();

    // Parse and validate request body
    const parseResult = AttachSubstrateRequestSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: 'Invalid request body', details: parseResult.error.flatten() },
        { status: 422 }
      );
    }

    const { substrate_type, substrate_id, role, weight, snippets, metadata } = parseResult.data;
    const supabase = createServerSupabaseClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // Verify document access
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('id, basket_id, workspace_id')
      .eq('id', id)
      .maybeSingle();

    if (docError || !document) {
      return NextResponse.json({ error: 'document not found' }, { status: 404 });
    }

    if (document.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'unauthorized' }, { status: 403 });
    }

    // Call database function to attach substrate
    const { data: referenceId, error: attachError } = await supabase
      .rpc('fn_document_attach_substrate', {
        p_document_id: id,
        p_substrate_type: substrate_type,
        p_substrate_id: substrate_id,
        p_role: role,
        p_weight: weight,
        p_snippets: snippets || [],
        p_metadata: metadata || {}
      });

    if (attachError) {
      console.error('Attachment error:', attachError);
      // Check if it's a unique constraint violation (substrate already attached)
      if (attachError.code === '23505' || attachError.message.includes('unique constraint')) {
        return NextResponse.json(
          { error: `Substrate already attached to document` },
          { status: 409 }
        );
      }
      return NextResponse.json(
        { error: `Failed to attach substrate: ${attachError.message}` },
        { status: 400 }
      );
    }

    // Fetch the created reference
    const { data: reference, error: fetchError } = await supabase
      .from('substrate_references')
      .select('*')
      .eq('id', referenceId)
      .single();

    if (fetchError || !reference) {
      console.error('Error fetching created reference:', fetchError);
      return NextResponse.json({ error: 'Reference created but could not be retrieved' }, { status: 500 });
    }

    const referenceDTO: SubstrateReferenceDTO = {
      id: reference.id,
      document_id: reference.document_id,
      substrate_type: reference.substrate_type,
      substrate_id: reference.substrate_id,
      role: reference.role,
      weight: reference.weight,
      snippets: reference.snippets || [],
      metadata: reference.metadata || {},
      created_at: reference.created_at,
      created_by: reference.created_by
    };

    const response: AttachSubstrateResponse = {
      reference: referenceDTO
    };

    return withSchema(AttachSubstrateResponseSchema, response, { status: 201 });

  } catch (error) {
    console.error('Substrate attachment error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

// DELETE /api/documents/[id]/references?substrate_type=X&substrate_id=Y
export async function DELETE(
  request: NextRequest,
  ctx: RouteContext
) {
  try {
    const { id } = await ctx.params;
    const url = new URL(request.url);
    const substrate_type = url.searchParams.get('substrate_type');
    const substrate_id = url.searchParams.get('substrate_id');

    if (!substrate_type || !substrate_id) {
      return NextResponse.json(
        { error: 'substrate_type and substrate_id query parameters are required' },
        { status: 400 }
      );
    }

    const supabase = createServerSupabaseClient();
    const { userId, isTest } = await getTestAwareAuth(supabase);
    const workspace = isTest ? { id: '00000000-0000-0000-0000-000000000002' } : await ensureWorkspaceForUser(userId, supabase);

    // Verify document access
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('id, workspace_id')
      .eq('id', id)
      .maybeSingle();

    if (docError || !document) {
      return NextResponse.json({ error: 'document not found' }, { status: 404 });
    }

    if (document.workspace_id !== workspace.id) {
      return NextResponse.json({ error: 'unauthorized' }, { status: 403 });
    }

    // Call database function to detach substrate
    const { data: success, error: detachError } = await supabase
      .rpc('fn_document_detach_substrate', {
        p_document_id: id,
        p_substrate_type: substrate_type,
        p_substrate_id: substrate_id
      });

    if (detachError) {
      console.error('Detachment error:', detachError);
      return NextResponse.json(
        { error: `Failed to detach substrate: ${detachError.message}` },
        { status: 400 }
      );
    }

    if (!success) {
      return NextResponse.json({ error: 'Reference not found' }, { status: 404 });
    }

    return NextResponse.json({ success: true }, { status: 200 });

  } catch (error) {
    console.error('Substrate detachment error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}