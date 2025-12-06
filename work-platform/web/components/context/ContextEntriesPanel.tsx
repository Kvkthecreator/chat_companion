"use client";

/**
 * ContextEntriesPanel - Windows Explorer-style context management
 *
 * Architecture (Phase 2 Refactor):
 * - Two view modes: List (table-style, data-dense) and Grid (card previews)
 * - Click ANY row navigates to detail page (including empty = create)
 * - No modals - all editing happens on detail page
 * - Realtime updates via Supabase
 *
 * See: /docs/architecture/ADR_CONTEXT_ITEMS_UNIFIED.md
 */

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  Plus,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Users,
  Eye,
  Palette,
  Target,
  TrendingUp,
  BarChart3,
  Loader2,
  RefreshCw,
  User,
  Bot,
  Sparkles,
  Lightbulb,
  List,
  LayoutGrid,
  ChevronRight,
  FileText,
} from 'lucide-react';
import {
  useContextSchemas,
  useContextEntries,
  type ContextEntrySchema,
  type ContextEntry,
} from '@/hooks/useContextEntries';
import { useContextItemsRealtime } from '@/hooks/useTPRealtime';

// =============================================================================
// CONSTANTS & CONFIG
// =============================================================================

type ViewMode = 'list' | 'grid';

const ROLE_ICONS: Record<string, React.ElementType> = {
  problem: AlertTriangle,
  customer: Users,
  vision: Eye,
  brand: Palette,
  competitor: Target,
  trend_digest: TrendingUp,
  market_intel: Lightbulb,
  competitor_snapshot: BarChart3,
};

const TIER_CONFIG: Record<string, { label: string; color: string; bgColor: string }> = {
  foundation: { label: 'Foundation', color: 'text-blue-700', bgColor: 'bg-blue-500/10 border-blue-500/30' },
  working: { label: 'Working', color: 'text-purple-700', bgColor: 'bg-purple-500/10 border-purple-500/30' },
  ephemeral: { label: 'Ephemeral', color: 'text-gray-600', bgColor: 'bg-gray-500/10 border-gray-500/30' },
};

const ITEM_TYPE_LABELS: Record<string, string> = {
  trend_digest: 'Trend Digest',
  market_intel: 'Market Intelligence',
  competitor_snapshot: 'Competitor Snapshot',
  problem: 'Problem',
  customer: 'Customer',
  vision: 'Vision',
  brand: 'Brand Identity',
  competitor: 'Competitor',
};

const CATEGORY_CONFIG = {
  foundation: {
    title: 'Foundation',
    description: 'Core context that defines your project',
    color: 'bg-blue-500',
  },
  market: {
    title: 'Market Intelligence',
    description: 'Competitive landscape and market data',
    color: 'bg-purple-500',
  },
  insight: {
    title: 'Agent Insights',
    description: 'AI-generated analysis and recommendations',
    color: 'bg-green-500',
  },
};

// =============================================================================
// MAIN COMPONENT
// =============================================================================

interface ContextEntriesPanelProps {
  projectId: string;
  basketId: string;
  initialAnchorRole?: string;
}

export default function ContextEntriesPanel({
  projectId,
  basketId,
  initialAnchorRole,
}: ContextEntriesPanelProps) {
  const router = useRouter();

  // View mode state - persisted to localStorage
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('context-view-mode') as ViewMode) || 'list';
    }
    return 'list';
  });

  // Persist view mode
  useEffect(() => {
    localStorage.setItem('context-view-mode', viewMode);
  }, [viewMode]);

  // Fetch schemas and entries
  const {
    schemas,
    schemasByCategory,
    loading: schemasLoading,
    error: schemasError,
    refetch: refetchSchemas,
  } = useContextSchemas(basketId);

  const {
    entries,
    loading: entriesLoading,
    error: entriesError,
    refetch: refetchEntries,
    getEntryByRole,
  } = useContextEntries(basketId);

  // Realtime updates
  useContextItemsRealtime(basketId, () => {
    refetchEntries();
  });

  // Navigate to detail page (existing item)
  const navigateToDetail = (entryId: string) => {
    router.push(`/projects/${projectId}/context/${entryId}`);
  };

  // Navigate to create page (new item)
  const navigateToCreate = (schemaRole: string) => {
    router.push(`/projects/${projectId}/context/new/${schemaRole}`);
  };

  // Calculate overall completeness
  const overallCompleteness = useMemo(() => {
    const foundationSchemas = schemasByCategory.foundation;
    if (foundationSchemas.length === 0) return 0;

    let filled = 0;
    foundationSchemas.forEach((schema) => {
      const entry = getEntryByRole(schema.anchor_role);
      if (entry && Object.keys(entry.data).length > 0) {
        filled++;
      }
    });

    return filled / foundationSchemas.length;
  }, [schemasByCategory.foundation, getEntryByRole]);

  // Filter agent-generated working-tier insights
  const agentInsights = useMemo(() => {
    return entries.filter(
      (entry) =>
        entry.tier === 'working' &&
        entry.source_type === 'agent' &&
        ['trend_digest', 'market_intel', 'competitor_snapshot'].includes(entry.anchor_role)
    );
  }, [entries]);

  const loading = schemasLoading || entriesLoading;
  const error = schemasError || entriesError;

  if (loading && schemas.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <AlertCircle className="h-8 w-8 text-destructive mb-2" />
        <p className="text-sm text-muted-foreground">{error}</p>
        <Button
          variant="outline"
          size="sm"
          className="mt-4"
          onClick={() => {
            refetchSchemas();
            refetchEntries();
          }}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with completeness + view toggle */}
      <div className="flex items-center gap-4">
        {/* Completeness bar */}
        <div className="flex-1 flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
          <div className="flex-1">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="font-medium">Foundation Completeness</span>
              <span className="text-muted-foreground">
                {Math.round(overallCompleteness * 100)}%
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${
                  overallCompleteness === 1
                    ? 'bg-green-500'
                    : overallCompleteness >= 0.5
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${overallCompleteness * 100}%` }}
              />
            </div>
          </div>
          {overallCompleteness === 1 ? (
            <CheckCircle className="h-6 w-6 text-green-500" />
          ) : (
            <AlertCircle className="h-6 w-6 text-muted-foreground" />
          )}
        </div>

        {/* View mode toggle */}
        <div className="flex items-center border rounded-lg p-1 bg-muted/30">
          <Button
            variant={viewMode === 'list' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-8 px-3"
            onClick={() => setViewMode('list')}
            title="List view"
          >
            <List className="h-4 w-4" />
          </Button>
          <Button
            variant={viewMode === 'grid' ? 'secondary' : 'ghost'}
            size="sm"
            className="h-8 px-3"
            onClick={() => setViewMode('grid')}
            title="Grid view"
          >
            <LayoutGrid className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Render each category */}
      {(Object.keys(CATEGORY_CONFIG) as Array<keyof typeof CATEGORY_CONFIG>).map((category) => {
        const config = CATEGORY_CONFIG[category];
        const categorySchemas = schemasByCategory[category];

        if (categorySchemas.length === 0) return null;

        return (
          <div key={category} className="space-y-3">
            {/* Category header */}
            <div className="flex items-center gap-3">
              <div className={`w-1 h-6 rounded-full ${config.color}`} />
              <div>
                <h3 className="font-semibold">{config.title}</h3>
                <p className="text-sm text-muted-foreground">{config.description}</p>
              </div>
            </div>

            {/* Items - List (table) or Grid view */}
            {viewMode === 'list' ? (
              <ContextTable
                schemas={categorySchemas}
                getEntryByRole={getEntryByRole}
                onNavigate={navigateToDetail}
                onCreate={navigateToCreate}
              />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {categorySchemas.map((schema) => (
                  <ContextItemCard
                    key={schema.anchor_role}
                    schema={schema}
                    entry={getEntryByRole(schema.anchor_role) ?? null}
                    onNavigate={navigateToDetail}
                    onCreate={navigateToCreate}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}

      {/* Agent Insights Section */}
      {agentInsights.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-1 h-6 rounded-full bg-purple-500" />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">Agent Insights</h3>
                <Badge variant="secondary" className="text-xs">
                  {agentInsights.length}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">
                AI-generated analysis from scheduled research
              </p>
            </div>
          </div>

          {viewMode === 'list' ? (
            <AgentInsightsTable
              entries={agentInsights}
              onNavigate={navigateToDetail}
            />
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {agentInsights.map((entry) => (
                <AgentInsightCard
                  key={entry.id}
                  entry={entry}
                  onNavigate={navigateToDetail}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// TABLE VIEW COMPONENT (True List Style)
// =============================================================================

function ContextTable({
  schemas,
  getEntryByRole,
  onNavigate,
  onCreate,
}: {
  schemas: ContextEntrySchema[];
  getEntryByRole: (role: string) => ContextEntry | undefined;
  onNavigate: (id: string) => void;
  onCreate: (schemaRole: string) => void;
}) {
  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-muted/50 border-b">
            <th className="text-left py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Name
            </th>
            <th className="text-left py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide w-24">
              Source
            </th>
            <th className="text-left py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide w-28">
              Updated
            </th>
            <th className="text-left py-2.5 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Preview
            </th>
            <th className="w-10"></th>
          </tr>
        </thead>
        <tbody>
          {schemas.map((schema) => {
            const entry = getEntryByRole(schema.anchor_role);
            const hasContent = entry && Object.keys(entry.data).length > 0;
            const Icon = ROLE_ICONS[schema.anchor_role] || FileText;

            return (
              <tr
                key={schema.anchor_role}
                className={`border-b last:border-b-0 cursor-pointer transition-colors ${
                  hasContent ? 'hover:bg-muted/50' : 'hover:bg-muted/30'
                }`}
                onClick={() => {
                  if (hasContent && entry) {
                    onNavigate(entry.id);
                  } else {
                    onCreate(schema.anchor_role);
                  }
                }}
              >
                {/* Name */}
                <td className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-1.5 rounded ${
                        hasContent ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className={`font-medium ${!hasContent ? 'text-muted-foreground' : ''}`}>
                      {schema.display_name}
                    </span>
                    {!hasContent && (
                      <Badge variant="outline" className="text-xs text-muted-foreground">
                        Empty
                      </Badge>
                    )}
                  </div>
                </td>

                {/* Source */}
                <td className="py-3 px-4">
                  {entry && <SourceBadge entry={entry} />}
                </td>

                {/* Updated */}
                <td className="py-3 px-4 text-sm text-muted-foreground">
                  {entry ? formatRelativeDate(entry.updated_at) : '—'}
                </td>

                {/* Preview */}
                <td className="py-3 px-4 text-sm text-muted-foreground max-w-xs truncate">
                  {hasContent && entry
                    ? getContentPreview(entry.data, 60)
                    : <span className="italic">{schema.description}</span>
                  }
                </td>

                {/* Arrow */}
                <td className="py-3 px-4">
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// =============================================================================
// AGENT INSIGHTS TABLE
// =============================================================================

function AgentInsightsTable({
  entries,
  onNavigate,
}: {
  entries: ContextEntry[];
  onNavigate: (id: string) => void;
}) {
  return (
    <div className="border border-purple-500/20 rounded-lg overflow-hidden bg-purple-500/5">
      <table className="w-full">
        <thead>
          <tr className="bg-purple-500/10 border-b border-purple-500/20">
            <th className="text-left py-2.5 px-4 text-xs font-medium text-purple-700 uppercase tracking-wide">
              Name
            </th>
            <th className="text-left py-2.5 px-4 text-xs font-medium text-purple-700 uppercase tracking-wide w-24">
              Tier
            </th>
            <th className="text-left py-2.5 px-4 text-xs font-medium text-purple-700 uppercase tracking-wide w-24">
              Agent
            </th>
            <th className="text-left py-2.5 px-4 text-xs font-medium text-purple-700 uppercase tracking-wide w-28">
              Generated
            </th>
            <th className="text-left py-2.5 px-4 text-xs font-medium text-purple-700 uppercase tracking-wide">
              Summary
            </th>
            <th className="w-10"></th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => {
            const Icon = ROLE_ICONS[entry.anchor_role] || Sparkles;
            const typeLabel = ITEM_TYPE_LABELS[entry.anchor_role] || entry.anchor_role;
            const tierConfig = TIER_CONFIG[entry.tier || 'working'];
            const sourceRef = entry.source_ref as { agent_type?: string } | null;

            return (
              <tr
                key={entry.id}
                className="border-b border-purple-500/20 last:border-b-0 cursor-pointer hover:bg-purple-500/10 transition-colors"
                onClick={() => onNavigate(entry.id)}
              >
                {/* Name */}
                <td className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <div className="p-1.5 rounded bg-purple-500/10 text-purple-600">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="font-medium">{entry.display_name || typeLabel}</span>
                  </div>
                </td>

                {/* Tier */}
                <td className="py-3 px-4">
                  <Badge variant="outline" className={`text-xs ${tierConfig.bgColor} ${tierConfig.color}`}>
                    {tierConfig.label}
                  </Badge>
                </td>

                {/* Agent */}
                <td className="py-3 px-4">
                  <Badge variant="secondary" className="text-xs gap-1">
                    <Bot className="h-3 w-3" />
                    {sourceRef?.agent_type || 'Agent'}
                  </Badge>
                </td>

                {/* Generated */}
                <td className="py-3 px-4 text-sm text-muted-foreground">
                  {formatRelativeDate(entry.created_at)}
                </td>

                {/* Summary */}
                <td className="py-3 px-4 text-sm text-muted-foreground max-w-xs truncate">
                  {getContentPreview(entry.data, 80)}
                </td>

                {/* Arrow */}
                <td className="py-3 px-4">
                  <ChevronRight className="h-4 w-4 text-purple-600" />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// =============================================================================
// GRID VIEW COMPONENTS
// =============================================================================

function ContextItemCard({
  schema,
  entry,
  onNavigate,
  onCreate,
}: {
  schema: ContextEntrySchema;
  entry: ContextEntry | null;
  onNavigate: (id: string) => void;
  onCreate: (schemaRole: string) => void;
}) {
  const Icon = ROLE_ICONS[schema.anchor_role] || FileText;
  const hasContent = entry && Object.keys(entry.data).length > 0;

  return (
    <Card
      className={`group flex flex-col h-full transition-all cursor-pointer ${
        hasContent
          ? 'hover:shadow-md hover:border-primary/30'
          : 'border-dashed hover:border-primary/50 hover:bg-muted/30'
      }`}
      onClick={() => {
        if (hasContent && entry) {
          onNavigate(entry.id);
        } else {
          onCreate(schema.anchor_role);
        }
      }}
    >
      {/* Header */}
      <div className="flex items-start gap-3 p-4 pb-2">
        <div
          className={`p-2.5 rounded-lg shrink-0 ${
            hasContent ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'
          }`}
        >
          <Icon className="h-6 w-6" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium leading-tight">{schema.display_name}</h4>
          {entry && (
            <div className="mt-1">
              <SourceBadge entry={entry} />
            </div>
          )}
        </div>
      </div>

      {/* Content preview */}
      <div className="flex-1 px-4 pb-4">
        {hasContent && entry ? (
          <div className="space-y-2">
            {getFieldPreviews(entry.data, schema.field_schema.fields).map((preview, idx) => (
              <div key={idx}>
                <p className="text-xs text-muted-foreground uppercase tracking-wide mb-0.5">
                  {preview.label}
                </p>
                {preview.type === 'array' ? (
                  <div className="flex flex-wrap gap-1">
                    {(preview.value as string[]).slice(0, 3).map((item, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {item}
                      </Badge>
                    ))}
                    {(preview.value as string[]).length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{(preview.value as string[]).length - 3}
                      </Badge>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-foreground line-clamp-2">
                    {preview.value as string}
                  </p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center py-4 text-center">
            <p className="text-sm text-muted-foreground mb-2">
              {schema.description}
            </p>
            <div className="flex items-center gap-1 text-sm text-primary">
              <Plus className="h-4 w-4" />
              Click to add
            </div>
          </div>
        )}
      </div>

      {/* Footer with timestamp */}
      {hasContent && entry && (
        <div className="px-4 py-2 border-t border-border/50 bg-muted/30">
          <p className="text-xs text-muted-foreground">
            Updated {formatRelativeDate(entry.updated_at)}
          </p>
        </div>
      )}
    </Card>
  );
}

function AgentInsightCard({
  entry,
  onNavigate,
}: {
  entry: ContextEntry;
  onNavigate: (id: string) => void;
}) {
  const Icon = ROLE_ICONS[entry.anchor_role] || Sparkles;
  const typeLabel = ITEM_TYPE_LABELS[entry.anchor_role] || entry.anchor_role;
  const tierConfig = TIER_CONFIG[entry.tier || 'working'];
  const sourceRef = entry.source_ref as { agent_type?: string } | null;

  return (
    <Card
      className="flex flex-col h-full cursor-pointer hover:shadow-md transition-all border-purple-500/20 bg-purple-500/5 hover:border-purple-500/40"
      onClick={() => onNavigate(entry.id)}
    >
      {/* Header */}
      <div className="flex items-start gap-3 p-4 pb-2">
        <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-600 shrink-0">
          <Icon className="h-6 w-6" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium leading-tight">{entry.display_name || typeLabel}</h4>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            <Badge variant="outline" className={`text-xs ${tierConfig.bgColor} ${tierConfig.color}`}>
              {tierConfig.label}
            </Badge>
            <Badge variant="secondary" className="text-xs gap-1">
              <Bot className="h-3 w-3" />
              {sourceRef?.agent_type || 'Agent'}
            </Badge>
          </div>
        </div>
      </div>

      {/* Content preview */}
      <div className="flex-1 px-4 pb-4">
        <p className="text-sm text-foreground line-clamp-4">
          {getContentPreview(entry.data, 200)}
        </p>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 border-t border-purple-500/20 bg-purple-500/5">
        <p className="text-xs text-muted-foreground">
          Generated {formatRelativeDate(entry.created_at)}
        </p>
      </div>
    </Card>
  );
}

// =============================================================================
// SHARED COMPONENTS
// =============================================================================

function SourceBadge({ entry }: { entry: ContextEntry }) {
  const updatedBy = entry.updated_by || entry.created_by;
  if (!updatedBy) return null;

  const isAgent = updatedBy.startsWith('agent:');
  const agentType = isAgent ? updatedBy.replace('agent:', '') : null;

  return (
    <Badge variant="outline" className="text-xs gap-1 font-normal">
      {isAgent ? (
        <>
          <Bot className="h-3 w-3" />
          <span>{agentType || 'Agent'}</span>
        </>
      ) : (
        <>
          <User className="h-3 w-3" />
          <span>You</span>
        </>
      )}
    </Badge>
  );
}

// =============================================================================
// UTILITIES
// =============================================================================

function getContentPreview(data: Record<string, unknown>, maxLength: number): string {
  const preferredFields = ['summary', 'description', 'statement', 'overview', 'content', 'body'];

  for (const field of preferredFields) {
    const value = data[field];
    if (typeof value === 'string' && value.length > 0) {
      return value.length > maxLength ? value.slice(0, maxLength) + '...' : value;
    }
  }

  for (const value of Object.values(data)) {
    if (typeof value === 'string' && value.length > 0) {
      return value.length > maxLength ? value.slice(0, maxLength) + '...' : value;
    }
  }

  return 'No content';
}

function getFieldPreviews(
  data: Record<string, unknown>,
  fields: Array<{ key: string; label: string; type: string }>
): Array<{ label: string; value: string | string[]; type: string }> {
  const previews: Array<{ label: string; value: string | string[]; type: string }> = [];
  const maxFields = 2;

  for (const field of fields) {
    if (previews.length >= maxFields) break;

    const value = data[field.key];
    if (!value) continue;

    if (Array.isArray(value) && value.length > 0) {
      previews.push({ label: field.label, value: value.map(String), type: 'array' });
    } else if (typeof value === 'string' && value.length > 0) {
      previews.push({
        label: field.label,
        value: value.length > 100 ? value.slice(0, 100) + '...' : value,
        type: 'text',
      });
    }
  }

  return previews;
}

function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;

  return date.toLocaleDateString();
}
