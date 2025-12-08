import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { notFound } from 'next/navigation';
import { DocumentsList } from '@/components/documents/DocumentsList';
import BasketSubpageLayout from '@/components/layouts/BasketSubpageLayout';
import { DocumentCreateButton } from '@/components/documents/DocumentCreateButton';
import { SectionCard } from '@/components/ui/SectionCard';
import { DocumentCanonBanner } from '@/components/canons/DocumentCanonBanner';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function DocumentsPage({ params }: PageProps) {
  const { id } = await params;
  
  // Authentication and workspace validation
  const supabase = createServerSupabaseClient();
  const { userId } = await getAuthenticatedUser(supabase);
  const workspace = await ensureWorkspaceForUser(userId, supabase);

  // Validate basket belongs to workspace
  const { data: basket, error: basketError } = await supabase
    .from('baskets')
    .select('id, name, workspace_id')
    .eq('id', id)
    .eq('workspace_id', workspace.id)
    .maybeSingle();

  if (basketError || !basket) {
    notFound();
  }

  return (
    <BasketSubpageLayout
      basketId={id}
      title="Documents"
      description="Compose and organize your documents"
      rightContent={<DocumentCreateButton basketId={id} basketName={basket.name} />}
    >
      <DocumentCanonBanner basketId={id} />
      <SectionCard>
        <DocumentsList basketId={id} />
      </SectionCard>
    </BasketSubpageLayout>
  );
}
