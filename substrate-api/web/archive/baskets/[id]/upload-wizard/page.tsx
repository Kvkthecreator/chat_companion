import { cookies } from 'next/headers';
import { notFound } from 'next/navigation';
import { createServerComponentClient } from '@/lib/supabase/clients';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { UploadWizard } from '@/components/wizard/UploadWizard';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function UploadWizardPage({ params }: PageProps) {
  const { id: basketId } = await params;
  const supabase = createServerComponentClient({ cookies });
  const { userId } = await getAuthenticatedUser(supabase);
  const workspace = await ensureWorkspaceForUser(userId, supabase);

  const { data: basket, error } = await supabase
    .from('baskets')
    .select('id, workspace_id, name, status')
    .eq('id', basketId)
    .maybeSingle();

  if (error || !basket || basket.workspace_id !== workspace.id) {
    notFound();
  }

  return (
    <UploadWizard
      basketId={basketId}
      basketName={basket.name || 'your basket'}
      maxDocuments={5}
      transformationMessage="Uploads become structured memory ingredients automatically."
    />
  );
}
