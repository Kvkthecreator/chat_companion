/**
 * Page: /projects/[id]/overview - Project Overview
 *
 * Primary project dashboard showing:
 * - Project metadata (name, description)
 * - Key metrics (context items, active work, completed work)
 * - Quick actions (create work request, add context, view reports)
 * - Context basket summary
 */
import { cookies } from "next/headers";
import { createServerComponentClient } from "@/lib/supabase/clients";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";
import { ProjectOverviewClient } from "./ProjectOverviewClient";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function ProjectOverviewPage({ params }: PageProps) {
  const { id: projectId } = await params;
  const supabase = createServerComponentClient({ cookies });
  const { userId } = await getAuthenticatedUser(supabase);

  // Fetch project (baskets are in separate DB, fetch separately via API)
  const { data: project } = await supabase
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
    .maybeSingle() as { data: any };

  if (!project) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-slate-900">Project not found</h2>
          <p className="mt-2 text-sm text-slate-600">
            The project you're looking for doesn't exist or you don't have access to it.
          </p>
        </div>
      </div>
    );
  }

  // Fetch agent sessions (pre-scaffolded during project creation)
  const { data: agentSessions } = await supabase
    .from('agent_sessions')
    .select('id, agent_type, workspace_id, basket_id, created_at, last_active_at, metadata')
    .eq('basket_id', project.basket_id)
    .order('created_at', { ascending: true });

  // Transform agent_sessions to match ProjectAgent interface
  const projectAgents = agentSessions?.map(session => ({
    id: session.id,
    agent_type: session.agent_type,
    display_name: getAgentDisplayName(session.agent_type),
    is_active: true, // All pre-scaffolded sessions are active
    created_at: session.created_at,
    last_active_at: session.last_active_at,
  })) || [];

  // Fetch work tickets stats (Phase 2e schema: work_tickets, not work_sessions)
  const { data: workTickets } = await supabase
    .from('work_tickets')
    .select('id, status, agent_type, created_at, updated_at, metadata')
    .eq('basket_id', project.basket_id);

  const sessionStats = {
    total: workTickets?.length || 0,
    pending: workTickets?.filter(t => t.status === 'pending').length || 0,
    running: workTickets?.filter(t => t.status === 'running').length || 0,
    paused: 0, // work_tickets doesn't have 'paused' status
    completed: workTickets?.filter(t => t.status === 'completed').length || 0,
    failed: workTickets?.filter(t => t.status === 'failed').length || 0,
  };

  // Fetch basket data from substrate-api via BFF pattern
  // Call our Next.js API route which proxies to substrate-api
  let blocksCount = 0;
  let documentsCount = 0;
  let basketName = project.name;
  let knowledgeBlocks = 0;
  let meaningBlocks = 0;

  try {
    const basketResponse = await fetch(
      `${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/api/baskets/${project.basket_id}`,
      {
        headers: {
          // Forward cookies for authentication
          Cookie: (await cookies()).toString(),
        },
        cache: 'no-store', // Always fetch fresh data
      }
    );

    if (basketResponse.ok) {
      const basketData = await basketResponse.json();
      blocksCount = basketData.stats?.blocks_count || 0;
      documentsCount = basketData.stats?.documents_count || 0;
      basketName = basketData.name || project.name;
    } else {
      console.warn(`[Project Overview] Failed to fetch basket ${project.basket_id}: ${basketResponse.status}`);
    }
  } catch (error) {
    console.error(`[Project Overview] Error fetching basket ${project.basket_id}:`, error);
    // Continue with 0 counts if fetch fails
  }

  try {
    const contextResponse = await fetch(
      `${process.env.NEXT_PUBLIC_SITE_URL || 'http://localhost:3000'}/api/projects/${project.id}/context`,
      {
        headers: {
          Cookie: (await cookies()).toString(),
        },
        cache: 'no-store',
      }
    );

    if (contextResponse.ok) {
      const contextData = await contextResponse.json();
      knowledgeBlocks = contextData?.stats?.knowledge || 0;
      meaningBlocks = contextData?.stats?.meaning || 0;
    }
  } catch (error) {
    console.warn('[Project Overview] Failed to fetch context stats:', error);
  }

  // Fetch pending review count (outputs awaiting supervision)
  const { count: pendingReviewCount } = await supabase
    .from('work_outputs')
    .select('id', { count: 'exact', head: true })
    .eq('basket_id', project.basket_id)
    .eq('supervision_status', 'pending_review');

  // Build agent-level stats from work_tickets (Phase 2e schema)
  // Map: agent_session_id → stats
  const agentStats: Record<string, {
    pending: number;
    running: number;
    lastRun: string | null;
    lastStatus: string | null;
    lastTask: string | null;
    lastSessionId: string | null;
  }> = {};

  agentSessions?.forEach((session) => {
    const ticketsForAgent = workTickets?.filter(t => t.agent_type === session.agent_type) || [];
    const pending = ticketsForAgent.filter(t => t.status === 'pending').length;
    const running = ticketsForAgent.filter(t => t.status === 'running').length;

    // Find most recent ticket for this agent type
    const sortedTickets = ticketsForAgent.sort((a, b) =>
      new Date(b.updated_at || b.created_at).getTime() -
      new Date(a.updated_at || a.created_at).getTime()
    );
    const lastTicket = sortedTickets[0];

    agentStats[session.id] = {
      pending,
      running,
      lastRun: lastTicket?.updated_at || lastTicket?.created_at || null,
      lastStatus: lastTicket?.status || null,
      lastTask: (lastTicket?.metadata as any)?.task_description || null,
      lastSessionId: lastTicket?.id || null,
    };
  });

  const projectData = {
    id: project.id,
    name: project.name,
    description: project.description,
    basket_id: project.basket_id,
    basket_name: basketName,
    status: project.status,
    workspace_id: project.workspace_id,
    user_id: project.user_id,
    created_at: project.created_at,
    updated_at: project.updated_at,
    agents: projectAgents || [],
    pendingReviewCount: pendingReviewCount || 0,
    stats: {
      contextItems: blocksCount || 0,
      documents: documentsCount || 0,
      knowledgeBlocks,
      meaningBlocks,
      workSessions: sessionStats,
      agents: agentStats,
    },
  };

  return (
    <div className="space-y-6 pb-8">
      <ProjectOverviewClient project={projectData} />
    </div>
  );
}

// Helper function to get display names for agent types
function getAgentDisplayName(agentType: string): string {
  switch (agentType) {
    case 'thinking_partner':
      return 'Thinking Partner';
    case 'research':
      return 'Research Agent';
    case 'content':
      return 'Content Agent';
    case 'reporting':
      return 'Reporting Agent';
    default:
      return agentType.charAt(0).toUpperCase() + agentType.slice(1) + ' Agent';
  }
}
