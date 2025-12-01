/**
 * Page: /projects/[id]/settings - Project Settings
 *
 * Project-level configuration including:
 * - General project metadata
 * - Basket statistics and management
 * - Danger zone (purge operations)
 */
import { cookies } from "next/headers";
import { createServerComponentClient } from "@/lib/supabase/clients";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";
import { notFound } from "next/navigation";
import { ProjectSettingsClient } from "./ProjectSettingsClient";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function ProjectSettingsPage({ params }: PageProps) {
  const { id: projectId } = await params;
  const supabase = createServerComponentClient({ cookies });
  const { userId } = await getAuthenticatedUser(supabase);

  // Fetch project
  const { data: project, error } = await supabase
    .from('projects')
    .select(`
      id,
      name,
      description,
      basket_id,
      workspace_id,
      user_id,
      status,
      created_at,
      updated_at
    `)
    .eq('id', projectId)
    .single();

  if (error || !project) {
    console.error('[Project Settings] Project not found:', error);
    notFound();
  }

  // Verify ownership
  if (project.user_id !== userId) {
    console.warn('[Project Settings] Access denied:', { userId, projectOwnerId: project.user_id });
    notFound();
  }

  // Fetch agent sessions (pre-scaffolded during project creation)
  const { data: agentSessions } = await supabase
    .from('agent_sessions')
    .select('id, agent_type, created_at, last_active_at, parent_session_id, created_by_session_id')
    .eq('basket_id', project.basket_id)
    .order('created_at', { ascending: true });

  // Fetch basket stats from substrate-api via BFF
  let basketStats = {
    blocks: 0,
    dumps: 0,
    assets: 0,
  };

  try {
    const previewResponse = await fetch(
      `${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/api/projects/${projectId}/purge/preview`,
      {
        headers: {
          Cookie: (await cookies()).toString(),
        },
        cache: 'no-store',
      }
    );

    if (previewResponse.ok) {
      basketStats = await previewResponse.json();
    } else {
      console.warn('[Project Settings] Failed to fetch basket stats:', previewResponse.status);
    }
  } catch (error) {
    console.error('[Project Settings] Error fetching basket stats:', error);
  }

  return (
    <div className="space-y-6 pb-8">
      <ProjectSettingsClient
        project={{
          id: project.id,
          name: project.name,
          description: project.description,
          basket_id: project.basket_id,
          status: project.status,
          created_at: project.created_at,
          updated_at: project.updated_at,
        }}
        basketStats={basketStats}
        agentSessions={agentSessions || []}
      />
    </div>
  );
}
