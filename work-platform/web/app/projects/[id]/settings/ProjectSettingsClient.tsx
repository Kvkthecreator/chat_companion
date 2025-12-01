'use client';

import { Settings as SettingsIcon, Zap, Copy, Check, Database, Shield, Boxes, AlertTriangle } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import SettingsSection from '@/components/settings/SettingsSection';
import DisplayBox from '@/components/settings/DisplayBox';
import { BasketDangerZone } from '@/components/projects/BasketDangerZone';
import { useMemo, useState } from 'react';

interface AgentSession {
  id: string;
  agent_type: string;
  created_at: string;
  last_active_at: string | null;
  parent_session_id: string | null;
  created_by_session_id: string | null;
}

interface ProjectSettingsClientProps {
  project: {
    id: string;
    name: string;
    description: string | null;
    basket_id: string;
    status: string;
    created_at: string;
    updated_at: string;
  };
  basketStats: {
    blocks: number;
    dumps: number;
    assets: number;
  };
  agentSessions: AgentSession[];
}

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

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="ml-2 p-1 hover:bg-slate-100 rounded transition-colors"
      title="Copy to clipboard"
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-green-600" />
      ) : (
        <Copy className="h-3.5 w-3.5 text-slate-400" />
      )}
    </button>
  );
}

export function ProjectSettingsClient({ project, basketStats, agentSessions }: ProjectSettingsClientProps) {
  const [tab, setTab] = useState<'general' | 'context' | 'agents' | 'danger'>('general');
  // Separate TP (parent) from specialists (children)
  const tpSession = agentSessions.find(s => s.agent_type === 'thinking_partner');
  const specialistSessions = agentSessions.filter(s => s.agent_type !== 'thinking_partner');
  const tabs = useMemo(
    () => [
      { key: 'general' as const, label: 'General', icon: SettingsIcon },
      { key: 'context' as const, label: 'Context', icon: Database },
      { key: 'agents' as const, label: 'Agents', icon: Boxes },
      { key: 'danger' as const, label: 'Danger', icon: AlertTriangle },
    ],
    [],
  );

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-6 py-8">
      {/* Header + summary */}
      <Card className="p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-muted">
              <SettingsIcon className="h-5 w-5 text-foreground" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-foreground">Project Settings</h1>
              <p className="text-sm text-muted-foreground">
                Streamlined controls for {project.name}
              </p>
            </div>
          </div>
          <Badge variant="secondary" className="capitalize">
            {project.status || 'active'}
          </Badge>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg border border-border/60 bg-card px-4 py-3">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Database className="h-4 w-4" />
              Context footprint
            </div>
            <div className="mt-2 text-sm text-foreground">
              {basketStats.blocks} blocks · {basketStats.dumps} dumps · {basketStats.assets} assets
            </div>
          </div>
          <div className="rounded-lg border border-border/60 bg-card px-4 py-3">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Shield className="h-4 w-4" />
              Basket
            </div>
            <div className="mt-2 flex items-center gap-2 text-sm text-foreground">
              <span className="truncate font-mono text-xs sm:text-sm">{project.basket_id}</span>
              <CopyButton text={project.basket_id} />
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-sm transition ${
              tab === key
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-border text-muted-foreground hover:text-foreground'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'general' && (
        <SettingsSection
          title="General"
          description="Project metadata and identifiers"
        >
          <div className="grid gap-4 md:grid-cols-2">
            <DisplayBox label="Project ID" value={project.id} />
            <DisplayBox label="Name" value={project.name} />
            {project.description && (
              <DisplayBox label="Description" value={project.description} />
            )}
            <DisplayBox
              label="Created"
              value={new Date(project.created_at).toLocaleString()}
            />
            <DisplayBox
              label="Updated"
              value={new Date(project.updated_at).toLocaleString()}
            />
          </div>
        </SettingsSection>
      )}

      {tab === 'context' && (
        <SettingsSection
          title="Context Storage"
          description="Basket statistics and substrate data"
        >
          <div className="grid gap-4 md:grid-cols-2">
            <DisplayBox label="Basket ID" value={project.basket_id} />
            <DisplayBox
              label="Context Blocks"
              value={`${basketStats.blocks} block${basketStats.blocks !== 1 ? 's' : ''}`}
            />
            <DisplayBox
              label="Raw Dumps"
              value={`${basketStats.dumps} dump${basketStats.dumps !== 1 ? 's' : ''}`}
            />
            <DisplayBox
              label="Uploaded Assets"
              value={`${basketStats.assets} asset${basketStats.assets !== 1 ? 's' : ''}`}
            />
          </div>
          <div className="mt-3 rounded-md border border-border bg-muted/40 p-4 text-xs text-muted-foreground">
            Context blocks are extracted knowledge. Raw dumps are source materials before processing. Assets are uploaded files (images, documents, etc.).
          </div>
        </SettingsSection>
      )}

      {tab === 'agents' && (
        <SettingsSection
          title="Agent Infrastructure"
          description="Pre-scaffolded agent sessions and hierarchy"
        >
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-muted-foreground">
              All agent sessions created during project setup
            </div>
            <Badge variant="secondary" className="gap-2 bg-green-500/10 text-green-700 border-green-500/20">
              {agentSessions.length} session{agentSessions.length === 1 ? '' : 's'}
            </Badge>
          </div>

          {/* Thinking Partner (Root Session) */}
          {tpSession && (
            <div className="mt-4 rounded-lg border border-border bg-card p-4 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="rounded-lg bg-primary/10 p-2">
                  <Zap className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-foreground">{getAgentDisplayName(tpSession.agent_type)}</h4>
                    <Badge variant="outline" className="text-xs">
                      Root Session
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Orchestrates all specialist agents</p>
                </div>
              </div>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <div className="rounded border border-border/70 bg-muted/50 px-3 py-2 text-xs">
                  <div className="text-muted-foreground">Session ID</div>
                  <div className="mt-1 flex items-center gap-2 font-mono text-[11px] text-foreground">
                    <span className="truncate">{tpSession.id}</span>
                    <CopyButton text={tpSession.id} />
                  </div>
                </div>
                <div className="rounded border border-border/70 bg-muted/50 px-3 py-2 text-xs">
                  <div className="text-muted-foreground">Created</div>
                  <div className="mt-1 text-foreground">{new Date(tpSession.created_at).toLocaleString()}</div>
                </div>
                {tpSession.last_active_at && (
                  <div className="rounded border border-border/70 bg-muted/50 px-3 py-2 text-xs">
                    <div className="text-muted-foreground">Last Active</div>
                    <div className="mt-1 text-foreground">{new Date(tpSession.last_active_at).toLocaleString()}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Specialist Sessions */}
          {specialistSessions.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-sm font-medium text-foreground">Specialist Agents</h4>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {specialistSessions.map((session) => (
                  <div key={session.id} className="rounded-lg border border-border bg-card p-3 shadow-sm">
                    <div className="flex items-center gap-2">
                      <div className="rounded bg-muted p-1.5">
                        <Zap className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h5 className="text-sm font-medium text-foreground truncate">
                          {getAgentDisplayName(session.agent_type)}
                        </h5>
                      </div>
                    </div>
                    <div className="mt-2 space-y-2 text-[11px]">
                      <div className="rounded border border-border/70 bg-muted/40 px-2 py-1.5">
                        <div className="text-muted-foreground">Session ID</div>
                        <div className="mt-1 flex items-center gap-2">
                          <code className="truncate">{session.id.split('-')[0]}...</code>
                          <CopyButton text={session.id} />
                        </div>
                      </div>
                      {session.parent_session_id && (
                        <div className="rounded border border-border/70 bg-muted/40 px-2 py-1.5">
                          <div className="text-muted-foreground">Parent Session</div>
                          <code className="mt-1 block truncate">{session.parent_session_id.split('-')[0]}...</code>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="mt-4 rounded-md border border-dashed border-border px-4 py-3 text-xs text-muted-foreground">
            Session IDs are useful for debugging and API integration. Thinking Partner orchestrates all specialist agents during work execution.
          </div>
        </SettingsSection>
      )}

      {tab === 'danger' && (
        <div>
          <SettingsSection
            title="Danger Zone"
            description="Purge context and reset this project"
          >
            <BasketDangerZone
              projectId={project.id}
              projectName={project.name}
              basketId={project.basket_id}
              basketStats={basketStats}
            />
          </SettingsSection>
        </div>
      )}
    </div>
  );
}
