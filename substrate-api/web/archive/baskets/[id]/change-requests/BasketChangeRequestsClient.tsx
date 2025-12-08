"use client";

import { useEffect, useMemo, useState, type ReactNode } from 'react';
import useSWR from 'swr';
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronRight,
  Clock,
  Database,
  Filter,
  FileText,
  Search,
  ShieldAlert,
  Sparkles,
  User,
} from 'lucide-react';
import { fetchWithToken } from '@/lib/fetchWithToken';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { ProposalDetailModal } from '@/components/governance/ProposalDetailModal';
import { generateProposalInsight, type ProposalInsight } from '@/lib/governance/proposalInsights';

interface ProposalOperation {
  type: string;
  data: Record<string, unknown>;
}

interface Proposal {
  id: string;
  proposal_kind: string;
  origin: 'agent' | 'human';
  source_host?: string | null;
  source_session?: string | null;
  status: 'PROPOSED' | 'APPROVED' | 'REJECTED';
  ops_summary: string;
  confidence: number;
  impact_summary: string;
  created_at: string;
  reviewed_at: string | null;
  executed_at: string | null;
  auto_approved: boolean;
  review_notes: string;
  is_executed: boolean;
  ops: ProposalOperation[];
  provenance: Array<string | Record<string, unknown>>;
  validator_report: {
    confidence: number;
    warnings: Array<string | Record<string, unknown>>;
    suggested_merges: string[];
    ontology_hits: string[];
    impact_summary?: string;
  };
}

interface ProposalsResponse {
  items: Proposal[];
}

const fetcher = (url: string) =>
  fetchWithToken(url).then((res) => {
    if (!res.ok) {
      throw new Error('Failed to load change requests');
    }
    return res.json();
  });

type StatusFilter = 'all' | 'PROPOSED' | 'APPROVED' | 'REJECTED';

const STATUS_CONTROLS: Array<{ key: StatusFilter; label: string }> = [
  { key: 'all', label: 'All' },
  { key: 'PROPOSED', label: 'Pending' },
  { key: 'APPROVED', label: 'Approved' },
  { key: 'REJECTED', label: 'Rejected' },
];

interface BasketChangeRequestsClientProps {
  basketId: string;
}

export default function BasketChangeRequestsClient({ basketId }: BasketChangeRequestsClientProps) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [showAutoOnly, setShowAutoOnly] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedProposalId, setSelectedProposalId] = useState<string | null>(null);

  const { data, error, isLoading, mutate } = useSWR<ProposalsResponse>(
    `/api/baskets/${basketId}/proposals${statusFilter === 'all' ? '' : `?status=${statusFilter}`}`,
    fetcher,
    { refreshInterval: 60_000 },
  );

  const proposals = data?.items ?? [];

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const openFromHash = () => {
      const hash = window.location.hash.replace('#', '');
      if (!hash) {
        setSelectedProposalId(null);
        return;
      }
      const match = proposals.find((proposal) => proposal.id === hash);
      if (match) {
        setSelectedProposalId(match.id);
      }
    };

    openFromHash();
    window.addEventListener('hashchange', openFromHash);
    return () => window.removeEventListener('hashchange', openFromHash);
  }, [proposals]);

  const filteredProposals = useMemo(() => {
    const text = query.trim().toLowerCase();
    return proposals
      .filter((proposal) => (showAutoOnly ? proposal.auto_approved : true))
      .filter((proposal) => {
        if (!text) return true;
        return (
          proposal.ops_summary.toLowerCase().includes(text) ||
          proposal.impact_summary.toLowerCase().includes(text) ||
          proposal.proposal_kind.toLowerCase().includes(text)
        );
      })
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [proposals, query, showAutoOnly]);

  const enrichedProposals = useMemo(
    () =>
      filteredProposals.map((proposal) => ({
        proposal,
        insight: generateProposalInsight({
          id: proposal.id,
          status: proposal.status,
          auto_approved: proposal.auto_approved,
          ops_summary: proposal.ops_summary,
          impact_summary: proposal.impact_summary,
          created_at: proposal.created_at,
          executed_at: proposal.executed_at,
          reviewed_at: proposal.reviewed_at,
          review_notes: proposal.review_notes,
          provenance: proposal.provenance,
          validator_report: proposal.validator_report,
          ops: proposal.ops,
        }),
      })),
    [filteredProposals],
  );

  const stats = useMemo(() => {
    const total = proposals.length;
    const pending = proposals.filter((p) => p.status === 'PROPOSED').length;
    const approved = proposals.filter((p) => p.status === 'APPROVED').length;
    const rejected = proposals.filter((p) => p.status === 'REJECTED').length;
    const autoApproved = proposals.filter((p) => p.auto_approved).length;
    const highImpact = proposals.filter((p) => p.validator_report.warnings.length > 0 || p.validator_report.confidence < 0.6).length;

    return { total, pending, approved, rejected, autoApproved, highImpact };
  }, [proposals]);

  const openProposalDetail = (proposalId: string) => {
    setSelectedProposalId(proposalId);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.hash = proposalId;
      window.history.replaceState(null, '', url.toString());
    }
  };

  const closeProposalDetail = () => {
    setSelectedProposalId(null);
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.hash = '';
      window.history.replaceState(null, '', url.pathname + url.search);
    }
  };

  const handleApprove = async (proposalId: string, notes?: string) => {
    try {
      const response = await fetch(`/api/baskets/${basketId}/proposals/${proposalId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_notes: notes || 'Approved via governance queue' }),
      });
      if (!response.ok) {
        throw new Error(`Approve failed: ${response.status}`);
      }
      mutate();
    } catch (err) {
      console.error('Failed to approve proposal', err);
    }
  };

  const handleReject = async (proposalId: string, reason: string) => {
    try {
      const response = await fetch(`/api/baskets/${basketId}/proposals/${proposalId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_notes: 'Rejected via governance queue', reason }),
      });
      if (!response.ok) {
        throw new Error(`Reject failed: ${response.status}`);
      }
      mutate();
    } catch (err) {
      console.error('Failed to reject proposal', err);
    }
  };

  if (error) {
    return (
      <Card className="border-red-200 bg-red-50">
        <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
          <AlertTriangle className="h-8 w-8 text-red-600" />
          <div>
            <p className="text-lg font-semibold text-red-700">Unable to load change requests</p>
            <p className="text-sm text-red-600">{error.message}</p>
          </div>
          <Button onClick={() => mutate()} variant="outline">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-32 animate-pulse rounded-xl bg-gray-100" />
        <div className="h-48 animate-pulse rounded-xl bg-gray-100" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Total proposals"
          value={stats.total}
          icon={<FileText className="h-5 w-5 text-slate-500" />}
          onClick={() => setStatusFilter('all')}
          active={statusFilter === 'all'}
        />
        <StatCard
          title="Pending review"
          value={stats.pending}
          tone="warning"
          icon={<Clock className="h-5 w-5 text-amber-500" />}
          onClick={() => setStatusFilter('PROPOSED')}
          active={statusFilter === 'PROPOSED'}
        />
        <StatCard
          title="Approved"
          value={stats.approved}
          tone="success"
          icon={<CheckCircle2 className="h-5 w-5 text-emerald-500" />}
          onClick={() => setStatusFilter('APPROVED')}
          active={statusFilter === 'APPROVED'}
        />
        <StatCard
          title="Rejected"
          value={stats.rejected}
          tone="danger"
          icon={<ShieldAlert className="h-5 w-5 text-rose-500" />}
          onClick={() => setStatusFilter('REJECTED')}
          active={statusFilter === 'REJECTED'}
        />
        <StatCard
          title="Auto-approved"
          value={stats.autoApproved}
          tone="accent"
          icon={<Bot className="h-5 w-5 text-purple-500" />}
          active={showAutoOnly}
          onClick={() => {
            setShowAutoOnly((prev) => !prev);
            setStatusFilter('all');
          }}
        />
        <StatCard
          title="Needs attention"
          value={stats.highImpact}
          tone="alert"
          icon={<AlertTriangle className="h-5 w-5 text-orange-500" />}
          onClick={() => {
            setStatusFilter('PROPOSED');
            setShowAutoOnly(false);
          }}
        />
      </section>

      <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-wrap gap-2">
            {STATUS_CONTROLS.map(({ key, label }) => (
              <Button
                key={key}
                size="sm"
                variant={statusFilter === key ? 'primary' : 'outline'}
                onClick={() => setStatusFilter(key)}
              >
                {label}
              </Button>
            ))}
            <Button
              size="sm"
              variant={showAutoOnly ? 'primary' : 'outline'}
              onClick={() => setShowAutoOnly((prev) => !prev)}
              className="flex items-center gap-1"
            >
              <Filter className="h-3.5 w-3.5" />
              Auto-approved
            </Button>
          </div>
          <div className="relative max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search proposals"
              className="pl-9"
            />
          </div>
        </div>

        {enrichedProposals.length === 0 ? (
          <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-slate-200 py-12 text-center">
            <FileText className="h-10 w-10 text-slate-300" />
            <p className="text-base font-medium text-slate-700">No change requests found</p>
            <p className="max-w-sm text-sm text-slate-500">
              Adjust your filters or capture new memory to generate substrate proposals.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {enrichedProposals.map(({ proposal, insight }) => (
              <ProposalCard
                key={proposal.id}
                proposal={proposal}
                insight={insight}
                onReview={() => openProposalDetail(proposal.id)}
              />
            ))}
          </div>
        )}
      </section>

      <ProposalDetailModal
        basketId={basketId}
        isOpen={Boolean(selectedProposalId)}
        proposalId={selectedProposalId}
        onClose={closeProposalDetail}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: ReactNode;
  tone?: 'success' | 'warning' | 'danger' | 'accent' | 'alert';
  onClick?: () => void;
  active?: boolean;
}

function StatCard({ title, value, icon, tone, onClick, active }: StatCardProps) {
  const palette = {
    success: {
      border: 'border-emerald-200',
      icon: 'bg-emerald-50 text-emerald-600',
    },
    warning: {
      border: 'border-amber-200',
      icon: 'bg-amber-50 text-amber-600',
    },
    danger: {
      border: 'border-rose-200',
      icon: 'bg-rose-50 text-rose-600',
    },
    accent: {
      border: 'border-purple-200',
      icon: 'bg-purple-50 text-purple-600',
    },
    alert: {
      border: 'border-orange-200',
      icon: 'bg-orange-50 text-orange-600',
    },
  } as const;

  const borderClass = tone ? palette[tone].border : 'border-slate-200';
  const iconClass = tone ? palette[tone].icon : 'bg-slate-100 text-slate-500';

  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full rounded-lg border ${borderClass} bg-white px-4 py-3 text-left shadow-sm transition-colors ${
        active ? 'ring-2 ring-slate-300' : 'hover:border-slate-300'
      }`}
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-wide text-slate-500">{title}</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
        </div>
        <div className={`rounded-md p-2 text-sm ${iconClass}`}>
          {icon}
        </div>
      </div>
    </button>
  );
}

interface ProposalCardProps {
  proposal: Proposal;
  insight: ProposalInsight;
  onReview: () => void;
}

function ProposalCard({ proposal, insight, onReview }: ProposalCardProps) {
  const statusTone = proposal.status === 'APPROVED'
    ? 'border-emerald-200 text-emerald-700'
    : proposal.status === 'PROPOSED'
      ? 'border-amber-200 text-amber-700'
      : 'border-rose-200 text-rose-700';

  const originBadge = proposal.origin === 'agent'
    ? {
        label: proposal.source_host || 'Ambient agent',
        className: 'bg-purple-50 text-purple-700 border-purple-200',
        icon: <Bot className="h-3.5 w-3.5" />,
      }
    : { label: 'Human initiated', className: 'bg-blue-50 text-blue-700 border-blue-200', icon: <User className="h-3.5 w-3.5" /> };

  const riskBorder =
    insight.riskLevel === 'high'
      ? 'border-rose-200'
      : insight.riskLevel === 'medium'
        ? 'border-amber-200'
        : 'border-slate-200';

  const submittedAt = new Date(proposal.created_at).toLocaleString();

  return (
    <Card className={`border ${riskBorder} bg-white shadow-sm transition-colors hover:border-slate-300`}>
      <CardHeader className="gap-3 border-b border-slate-100 pb-4">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className={`border ${statusTone} uppercase text-[11px] font-semibold`}>
            {proposal.status.toLowerCase()}
          </Badge>
          <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-200">
            {proposal.proposal_kind}
          </Badge>
          {proposal.auto_approved && (
            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
              Auto-approved
            </Badge>
          )}
          <Badge variant="outline" className={`${originBadge.className} flex items-center gap-1`}>
            {originBadge.icon}
            {originBadge.label}
          </Badge>
        </div>
        <CardTitle className="text-base font-semibold text-slate-900">{proposal.ops_summary}</CardTitle>
        <p className="text-sm text-slate-600">{proposal.impact_summary}</p>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Sparkles className="h-3.5 w-3.5 text-purple-500" />
          <span>{insight.confidenceLabel}</span>
          <span>•</span>
          <span className="capitalize">{insight.recommendation} recommendation</span>
          <span>•</span>
          <span>Submitted {submittedAt}</span>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-4 pt-4">
        <div className="rounded-lg border border-slate-100 bg-slate-50/70 p-4 text-sm leading-6 text-slate-700">
          <div className="mb-2 flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-purple-600">
            <Sparkles className="h-3.5 w-3.5" /> AI Insights
          </div>
          {insight.narrative}
        </div>

        <div className="flex flex-wrap gap-2">
          {insight.keyPoints.map((point) => (
            <Badge key={`${proposal.id}-${point}`} variant="outline" className="border-slate-200 bg-white text-xs text-slate-600">
              {point}
            </Badge>
          ))}
          {proposal.validator_report.warnings.length > 0 && (
            <Badge variant="outline" className="border-orange-200 bg-orange-50 text-orange-700 text-xs">
              {proposal.validator_report.warnings.length} warning{proposal.validator_report.warnings.length === 1 ? '' : 's'}
            </Badge>
          )}
        </div>

        <div className="flex flex-col gap-2 border-t border-slate-100 pt-4 text-sm text-slate-600 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
              <Database className="h-4 w-4 text-slate-400" />
              {insight.operationsSummary.replace(/\.$/, '')}
            </span>
            <span className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
              <Clock className="h-4 w-4 text-slate-400" />
              {proposal.provenance.length > 0
                ? `${proposal.provenance.length} reference${proposal.provenance.length === 1 ? '' : 's'} linked`
                : 'No references linked'}
            </span>
          </div>
          <div className="flex gap-2 sm:ml-auto">
            <Button variant="primary" size="sm" onClick={onReview} className="flex items-center gap-1">
              Review details
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
