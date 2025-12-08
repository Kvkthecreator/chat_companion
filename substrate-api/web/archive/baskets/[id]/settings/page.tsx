import type { Metadata } from 'next';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { notFound } from 'next/navigation';
import BasketSubpageLayout from '@/components/layouts/BasketSubpageLayout';
import DangerZoneClient from './DangerZoneClient';

export const metadata: Metadata = {
  title: 'Basket Settings',
  description: 'Manage basket-wide actions and maintenance',
};

interface PageProps { params: Promise<{ id: string }> }

export default async function BasketSettingsPage({ params }: PageProps) {
  const { id: basketId } = await params;
  try {
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    const { data: basket, error } = await supabase
      .from('baskets')
      .select('id, name, user_id, workspace_id')
      .eq('id', basketId)
      .maybeSingle();
    if (error || !basket || basket.workspace_id !== workspace.id) notFound();

    return (
      <BasketSubpageLayout
        basketId={basketId}
        title="Settings"
        description="Archive and redact basket contents, with safety and governance"
      >
        <DangerZoneClient basketId={basketId} basketName={basket.name || 'Untitled Basket'} />
      </BasketSubpageLayout>
    );
  } catch (e) {
    console.error('Basket Settings page error:', e);
    notFound();
  }
}

