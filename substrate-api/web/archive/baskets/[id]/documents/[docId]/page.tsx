import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { notFound } from 'next/navigation';
import { BasketWrapper } from '@/components/basket/BasketWrapper';
import { DocumentPage } from '@/components/documents/DocumentPage';

interface PageProps {
  params: Promise<{ id: string; docId: string }>;
}

export default async function DocumentDetailPage({ params }: PageProps) {
  const { id: basketId, docId } = await params;
  
  // Authentication and workspace validation
  const supabase = createServerSupabaseClient();
  const { userId } = await getAuthenticatedUser(supabase);
  const workspace = await ensureWorkspaceForUser(userId, supabase);

  const { data: documentRow, error: documentError } = await supabase
    .from('documents')
    .select('id, basket_id, workspace_id, title, current_version_hash, metadata, created_at, updated_at')
    .eq('id', docId)
    .maybeSingle();

  if (documentError || !documentRow) {
    notFound();
  }

  // Check workspace access and basket match
  if (documentRow.workspace_id !== workspace.id || documentRow.basket_id !== basketId) {
    notFound();
  }

  let versionContent: string | null = null;
  let versionMetadata: Record<string, any> | null = null;
  let versionCreatedAt: string | null = null;

  if (documentRow.current_version_hash) {
    const { data: version, error: versionError } = await supabase
      .from('document_versions')
      .select('content, metadata_snapshot, created_at')
      .eq('document_id', docId)
      .eq('version_hash', documentRow.current_version_hash)
      .maybeSingle();

    console.log('[DocumentDetailPage] Version fetch:', {
      docId,
      current_version_hash: documentRow.current_version_hash,
      hasVersion: !!version,
      hasContent: !!version?.content,
      contentLength: version?.content?.length || 0,
      versionError
    });

    if (version) {
      versionContent = version.content;
      versionMetadata = version.metadata_snapshot as Record<string, any> | null;
      versionCreatedAt = version.created_at;
    }
  }

  // Fetch additional basket data for context
  const { data: basketDetails } = await supabase
    .from('baskets')
    .select('name, description, status, created_at, last_activity_ts, tags, origin_template')
    .eq('id', basketId)
    .maybeSingle();

  // Create basket object with safe defaults
  const basket = {
    id: basketId,
    name: basketDetails?.name || 'Basket',
    workspace_id: workspace.id,
    description: basketDetails?.description || null,
    status: basketDetails?.status || null,
    created_at: basketDetails?.created_at || new Date().toISOString(),
    last_activity_ts: basketDetails?.last_activity_ts || null,
    tags: basketDetails?.tags || null,
    origin_template: basketDetails?.origin_template || null,
  };

  // Map document_heads view fields to DocumentPage expected format
  const documentForPage = {
    id: documentRow.id,
    basket_id: documentRow.basket_id,
    workspace_id: documentRow.workspace_id,
    title: documentRow.title,
    content: versionContent,
    created_at: documentRow.created_at,
    updated_at: documentRow.updated_at,
    metadata: {
      ...(documentRow.metadata || {}),
      ...(versionMetadata || {}),
      composition_completed_at: versionCreatedAt || documentRow.updated_at,
    },
  };

  console.log('[DocumentDetailPage] Passing to component:', {
    docId: documentForPage.id,
    hasContent: !!documentForPage.content,
    contentLength: documentForPage.content?.length || 0
  });

  return (
    <BasketWrapper basket={basket}>
      <DocumentPage document={documentForPage} basketId={basketId} />
    </BasketWrapper>
  );
}
