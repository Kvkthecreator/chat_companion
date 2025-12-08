export const dynamic = 'force-dynamic';

import type { Metadata } from 'next';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { notFound } from 'next/navigation';
import BasketSubpageLayout from '@/components/layouts/BasketSubpageLayout';
import { SectionCard } from '@/components/ui/SectionCard';
import NextDynamic from 'next/dynamic';

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Maintenance - Basket ${id}`,
    description: 'Suggest and propose safe archive/redact operations',
  };
}

const MaintenanceClient = NextDynamic(() => import('./MaintenanceClient').then(m => m.MaintenanceClient), {
  loading: () => <div className="h-64 animate-pulse" />,
});

export default async function MaintenancePage({ params }: { params: Promise<{ id: string }> }) {
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
        title="Maintenance"
        description="Review safe suggestions to archive or redact and convert them into proposals"
      >
        <SectionCard>
          <MaintenanceClient basketId={basketId} canEdit={basket.user_id === userId} />
        </SectionCard>
      </BasketSubpageLayout>
    );
  } catch (e) {
    console.error('Maintenance page error:', e);
    notFound();
  }
}
