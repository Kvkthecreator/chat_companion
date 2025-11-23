"use client";

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Plus, Zap, CheckCircle2, BookOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import CreateWorkRequestModal from '@/components/CreateWorkRequestModal';
import { formatDistanceToNow } from 'date-fns';

interface ProjectAgent {
  id: string;
  agent_type: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
}

interface ProjectData {
  id: string;
  name: string;
  description: string | null;
  basket_id: string;
  basket_name: string;
  status: string;
  workspace_id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  agents: ProjectAgent[];
  stats: {
    contextItems: number;
    documents: number;
    knowledgeBlocks: number;
    meaningBlocks: number;
    workSessions: {
      total: number;
      pending: number;
      running: number;
      paused: number;
      completed: number;
      failed: number;
    };
    agents: Record<string, {
      pending: number;
      running: number;
      lastRun: string | null;
      lastStatus: string | null;
      lastTask?: string | null;
      lastSessionId?: string | null;
    }>;
  };
}

interface ProjectOverviewClientProps {
  project: ProjectData;
}

export function ProjectOverviewClient({ project }: ProjectOverviewClientProps) {
  const router = useRouter();
  const [workRequestModalOpen, setWorkRequestModalOpen] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  const agentSummaries = useMemo(() => project.stats.agents || {}, [project.stats.agents]);

  const handleAgentClick = (agentId: string) => {
    setSelectedAgentId(agentId);
    setWorkRequestModalOpen(true);
  };

  const handleModalClose = (open: boolean) => {
    setWorkRequestModalOpen(open);
    if (!open) {
      setSelectedAgentId(null);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-6">
      {/* Project Header */}
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-foreground">{project.name}</h1>
            {project.description && (
              <p className="mt-2 text-lg text-muted-foreground">{project.description}</p>
            )}
            <div className="mt-3 flex items-center gap-4 text-sm text-muted-foreground">
              <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
              <span>•</span>
              <span>Updated {new Date(project.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
          <Badge variant="secondary" className="text-xs capitalize">
            {project.status}
          </Badge>
        </div>

      </div>

      {/* Project Agents */}
      {project.agents && project.agents.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">Agent Infrastructure</h3>
            <Badge variant="secondary" className="gap-2 bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {project.agents.length} Agents Ready
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            All agent sessions pre-scaffolded and ready for immediate use. No setup required.
          </p>
          <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
            {project.agents.map((agent) => {
              const stats = agentSummaries[agent.id];
              return (
                <div
                  key={agent.id}
                  className={cn(
                    'rounded-xl border bg-card p-4 transition-all flex flex-col gap-3',
                    agent.is_active ? 'hover:border-ring hover:shadow-md' : 'opacity-70'
                  )}
                >
                  <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-surface-primary/70 p-2 text-primary">
                        <Zap className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-foreground">{agent.display_name}</div>
                        <div className="text-xs text-muted-foreground capitalize">{agent.agent_type}</div>
                      </div>
                    </div>
                    <Badge variant="outline" className={cn('text-xs capitalize w-fit', getAgentStatusBadgeClass(stats, agent.is_active))}>
                      {getAgentStatusLabel(stats, agent.is_active)}
                    </Badge>
                  </div>
                  <div className="space-y-1 text-xs text-muted-foreground">
                    <p>
                      {stats?.lastRun
                        ? `Last run ${formatDistanceToNow(new Date(stats.lastRun))} ago`
                        : 'Session ready • Never used'}
                    </p>
                    {stats?.lastTask && (
                      <p className="line-clamp-2 text-foreground/80">“{stats.lastTask}”</p>
                    )}
                    {(stats?.pending || stats?.running) ? (
                      <p className="text-muted-foreground/90">
                        Queue: {stats.pending ?? 0} pending · {stats.running ?? 0} running
                      </p>
                    ) : null}
                  </div>
                  <div className="flex flex-col gap-2">
                    {/* Browse Recipes Button */}
                    {agent.is_active && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="w-full gap-2"
                        onClick={() => router.push(`/projects/${project.id}/agents/${agent.agent_type}/recipes`)}
                      >
                        <BookOpen className="h-4 w-4" />
                        Browse Recipes
                      </Button>
                    )}

                    {/* Legacy Actions */}
                    <div className="flex gap-2 flex-wrap">
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={!agent.is_active}
                        onClick={() => router.push(`/projects/${project.id}/agents/${agent.agent_type}`)}
                        className="text-xs flex-1"
                      >
                        Manage
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        className="gap-2 flex-1"
                        disabled={!agent.is_active}
                        onClick={() => handleAgentClick(agent.id)}
                      >
                        <Plus className="h-4 w-4" />
                        {getAgentQuickActionLabel(agent.agent_type)}
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Context Basket Info */}
      <Card className="p-6 border border-border bg-muted/60">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-muted-foreground">Linked Context</h3>
            <p className="text-lg font-medium text-foreground">{project.basket_name}</p>
            <p className="text-sm text-muted-foreground">
              Central knowledge base powering every agent in this project.
            </p>
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <p className="text-2xl font-semibold text-foreground">{project.stats.contextItems}</p>
                <p className="text-xs text-muted-foreground">Total Blocks</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-foreground">{project.stats.knowledgeBlocks}</p>
                <p className="text-xs text-muted-foreground">Knowledge Blocks</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-foreground">{project.stats.meaningBlocks}</p>
                <p className="text-xs text-muted-foreground">Meaning Blocks</p>
              </div>
            </div>
          </div>
          <Button
            size="sm"
            variant="ghost"
            className="self-start md:self-auto"
            onClick={() => router.push(`/projects/${project.id}/context`)}
          >
            View Context →
          </Button>
        </div>
      </Card>

      {/* Work Request Modal */}
      <CreateWorkRequestModal
        open={workRequestModalOpen}
        onOpenChange={handleModalClose}
        projectId={project.id}
        agents={project.agents}
        preSelectedAgentId={selectedAgentId}
      />
    </div>
  );
}

function getAgentQuickActionLabel(agentType: string) {
  switch (agentType) {
    case 'research':
      return 'Run Monitor';
    case 'content':
      return 'Create Content';
    case 'reporting':
      return 'Generate Report';
    default:
      return 'Start Work';
  }
}

function getAgentQuickActionHint(agentType: string) {
  switch (agentType) {
    case 'research':
      return 'Monitor markets or run a deep dive.';
    case 'content':
      return 'Draft posts, briefs, or copy.';
    case 'reporting':
      return 'Assemble summaries or decks.';
    default:
      return 'Kick off a new work session.';
  }
}

function getAgentStatusLabel(
  stats: { pending: number; running: number; lastStatus: string | null } | undefined,
  isActive: boolean
) {
  if (!isActive) return 'Inactive';
  if (!stats) return 'Ready'; // Changed from 'Idle' to 'Ready' for pre-scaffolded sessions
  if (stats.running > 0) return 'Running';
  if (stats.pending > 0) return 'Queued';
  if (stats.lastStatus) return stats.lastStatus.charAt(0).toUpperCase() + stats.lastStatus.slice(1);
  return 'Ready';
}

function getAgentStatusBadgeClass(
  stats: { pending: number; running: number; lastStatus: string | null } | undefined,
  isActive: boolean
) {
  const label = getAgentStatusLabel(stats, isActive).toLowerCase();
  if (label === 'running') {
    return 'bg-surface-primary/60 text-primary';
  }
  if (label === 'queued' || label === 'pending') {
    return 'bg-surface-warning/60 text-warning-foreground';
  }
  if (label === 'inactive') {
    return 'bg-muted text-muted-foreground';
  }
  if (label === 'ready') {
    return 'bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20';
  }
  return 'bg-surface-primary/20 text-primary';
}
