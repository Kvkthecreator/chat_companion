"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import {
  Anchor,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  ArrowRight,
  Users,
  Lightbulb,
  Eye,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface ContextReadinessCardProps {
  projectId: string;
  agentType: string;
}

type AnchorStats = {
  total: number;
  approved: number;
  draft: number;
  stale: number;
  missing: number;
};

type AnchorSummary = {
  anchor_key: string;
  lifecycle: string;
  label: string;
};

// Core anchors that agents need to work effectively
const CORE_ANCHOR_ROLES = ["problem", "customer", "vision"];

// Display config for core anchors
const ANCHOR_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; description: string }> = {
  problem: {
    label: "Problem",
    icon: AlertTriangle,
    description: "What pain point are you solving?",
  },
  customer: {
    label: "Customer",
    icon: Users,
    description: "Who is this for?",
  },
  vision: {
    label: "Vision",
    icon: Eye,
    description: "Where is this going?",
  },
};

export function ContextReadinessCard({ projectId, agentType }: ContextReadinessCardProps) {
  const [stats, setStats] = useState<AnchorStats | null>(null);
  const [anchors, setAnchors] = useState<AnchorSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/projects/${projectId}/context/anchors`);

        if (!response.ok) {
          throw new Error("Failed to fetch context status");
        }

        const data = await response.json();
        setStats(data.stats);
        setAnchors(data.anchors || []);
        setError(null);
      } catch (err) {
        console.error("[ContextReadinessCard] Error:", err);
        setError("Unable to check context");
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, [projectId]);

  // Determine readiness level
  const isReady = stats && stats.approved >= 3;
  const hasMinimal = stats && stats.approved >= 1;

  // Find missing core anchors
  const approvedAnchorKeys = anchors
    .filter(a => a.lifecycle === "approved")
    .map(a => a.anchor_key);
  const missingCoreAnchors = CORE_ANCHOR_ROLES.filter(
    role => !approvedAnchorKeys.includes(role)
  );

  if (loading) {
    return (
      <Card className="p-4">
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Checking context...</span>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-4 border-muted">
        <div className="flex items-center gap-3 text-muted-foreground">
          <AlertTriangle className="h-4 w-4" />
          <span className="text-sm">{error}</span>
        </div>
      </Card>
    );
  }

  return (
    <Card className={cn(
      "transition-colors overflow-hidden",
      isReady ? "border-green-500/30 bg-green-500/5" : "border-yellow-500/30 bg-yellow-500/5"
    )}>
      {/* Main header - always visible */}
      <button
        onClick={() => !isReady && setExpanded(!expanded)}
        disabled={isReady ?? false}
        className={cn(
          "w-full p-4 flex items-center justify-between gap-4",
          !isReady && "hover:bg-yellow-500/5 cursor-pointer"
        )}
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            "rounded-lg p-2",
            isReady ? "bg-green-500/10 text-green-600" : "bg-yellow-500/10 text-yellow-600"
          )}>
            {isReady ? (
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <Anchor className="h-5 w-5" />
            )}
          </div>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-foreground text-sm">Context</h3>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  isReady
                    ? "bg-green-500/10 text-green-700 border-green-500/30"
                    : "bg-yellow-500/10 text-yellow-700 border-yellow-500/30"
                )}
              >
                {isReady ? "Ready" : hasMinimal ? "Minimal" : "Needs Setup"}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {stats?.approved || 0} active anchor{stats?.approved !== 1 ? "s" : ""}
              {!isReady && missingCoreAnchors.length > 0 && ` • ${missingCoreAnchors.length} core missing`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {!isReady && (
            <>
              {expanded ? (
                <ChevronUp className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              )}
            </>
          )}
        </div>
      </button>

      {/* Expanded section showing missing anchors */}
      {expanded && !isReady && missingCoreAnchors.length > 0 && (
        <div className="px-4 pb-4 space-y-3">
          <div className="border-t border-yellow-500/20 pt-3">
            <p className="text-xs text-muted-foreground mb-3">
              Add these core anchors to help the agent understand your project:
            </p>
            <div className="space-y-2">
              {missingCoreAnchors.map((role) => {
                const config = ANCHOR_CONFIG[role];
                if (!config) return null;
                const IconComponent = config.icon;

                return (
                  <Link
                    key={role}
                    href={`/projects/${projectId}/context?add=${role}`}
                    className="flex items-center gap-3 p-3 rounded-lg border border-dashed border-yellow-500/30 bg-yellow-500/5 hover:bg-yellow-500/10 hover:border-yellow-500/50 transition-colors"
                  >
                    <div className="rounded-md p-1.5 bg-yellow-500/10 text-yellow-600">
                      <IconComponent className="h-4 w-4" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-foreground">{config.label}</p>
                      <p className="text-xs text-muted-foreground">{config.description}</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </Link>
                );
              })}
            </div>
          </div>

          <Link href={`/projects/${projectId}/context`}>
            <Button variant="outline" size="sm" className="w-full gap-1 text-xs border-yellow-500/30 text-yellow-700 hover:bg-yellow-500/10">
              Go to Context Page <ArrowRight className="h-3 w-3" />
            </Button>
          </Link>
        </div>
      )}
    </Card>
  );
}
