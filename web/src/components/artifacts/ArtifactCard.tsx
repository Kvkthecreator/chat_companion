"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  MapPin,
  Heart,
  MessageSquare,
  Users,
  Briefcase,
  Sparkles,
  Activity,
  BookOpen,
  ChevronRight,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import type { Artifact, ArtifactType } from "@/lib/api/client";
import { cn } from "@/lib/utils";

// Domain icons mapping
const DOMAIN_ICONS: Record<string, typeof Briefcase> = {
  career: Briefcase,
  location: MapPin,
  relationships: Heart,
  health: Activity,
  creative: Sparkles,
  life_stage: BookOpen,
  personal: Users,
};

// Artifact type configuration
const ARTIFACT_CONFIG: Record<ArtifactType, {
  icon: typeof Briefcase;
  title: string;
  description: string;
  gradient: string;
}> = {
  thread_journey: {
    icon: MapPin,
    title: "Thread Journey",
    description: "The story of a conversation thread",
    gradient: "from-blue-500/10 to-cyan-500/10",
  },
  domain_health: {
    icon: Activity,
    title: "Domain Health",
    description: "Activity across life areas",
    gradient: "from-green-500/10 to-emerald-500/10",
  },
  communication: {
    icon: MessageSquare,
    title: "How You Communicate",
    description: "Your communication patterns",
    gradient: "from-purple-500/10 to-pink-500/10",
  },
  relationship: {
    icon: Heart,
    title: "Our Relationship",
    description: "Summary of our time together",
    gradient: "from-rose-500/10 to-orange-500/10",
  },
};

interface ArtifactCardProps {
  artifact?: Artifact;
  artifactType?: ArtifactType;
  isLoading?: boolean;
  error?: Error | null;
  onClick?: () => void;
  onRegenerate?: () => void;
  compact?: boolean;
  showPreview?: boolean;
}

export function ArtifactCard({
  artifact,
  artifactType,
  isLoading,
  error,
  onClick,
  onRegenerate,
  compact = false,
  showPreview = true,
}: ArtifactCardProps) {
  const type = artifact?.artifact_type || artifactType;
  if (!type) return null;

  const config = ARTIFACT_CONFIG[type];
  const Icon = config.icon;

  // Get domain icon if this is a thread journey
  const DomainIcon = artifact?.domain ? DOMAIN_ICONS[artifact.domain] || Icon : Icon;

  if (isLoading) {
    return <ArtifactCardSkeleton compact={compact} />;
  }

  if (error) {
    return (
      <Card className={cn("border-destructive/50", compact && "p-3")}>
        <CardContent className={cn("flex items-center gap-3", compact ? "p-0" : "pt-6")}>
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p className="text-sm text-muted-foreground">Failed to load artifact</p>
        </CardContent>
      </Card>
    );
  }

  // Not enough data state
  if (artifact && !artifact.is_meaningful) {
    return (
      <Card className={cn(
        "relative overflow-hidden transition-all hover:shadow-md",
        compact && "p-3"
      )}>
        <div className={cn("absolute inset-0 bg-gradient-to-br opacity-50", config.gradient)} />
        <CardContent className={cn("relative", compact ? "p-0" : "pt-6")}>
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-muted/50 p-2">
              <Icon className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-muted-foreground">{config.title}</h3>
              <p className="text-sm text-muted-foreground/70 mt-1">
                {artifact.min_data_reason || "Not enough data yet"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      className={cn(
        "relative overflow-hidden transition-all cursor-pointer group",
        "hover:shadow-md hover:border-primary/30",
        compact && "p-3"
      )}
      onClick={onClick}
    >
      <div className={cn("absolute inset-0 bg-gradient-to-br", config.gradient)} />

      <CardContent className={cn("relative", compact ? "p-0" : "pt-6")}>
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-background/80 p-2 shadow-sm">
            <DomainIcon className="h-5 w-5 text-primary" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold truncate">
                {artifact?.title || config.title}
              </h3>
              {onRegenerate && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRegenerate();
                  }}
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>

            {showPreview && artifact?.companion_voice && (
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                "{artifact.companion_voice}"
              </p>
            )}

            {!compact && (
              <div className="flex items-center gap-2 mt-3 text-xs text-muted-foreground">
                <span>View full artifact</span>
                <ChevronRight className="h-3 w-3 group-hover:translate-x-0.5 transition-transform" />
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ArtifactCardSkeleton({ compact = false }: { compact?: boolean }) {
  return (
    <Card className={compact ? "p-3" : ""}>
      <CardContent className={cn("flex items-start gap-3", compact ? "p-0" : "pt-6")}>
        <Skeleton className="h-9 w-9 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-full" />
          {!compact && <Skeleton className="h-3 w-24 mt-3" />}
        </div>
      </CardContent>
    </Card>
  );
}

// Grid of artifact type cards for dashboard overview
interface ArtifactGridProps {
  availability: {
    thread_journey: { available: boolean; threads?: Array<{ thread_id: string; topic: string; domain?: string }> };
    domain_health: { available: boolean; domains?: Array<{ domain: string; thread_count: number }> };
    communication: { available: boolean; message_count?: number };
    relationship: { available: boolean; days_together?: number };
  } | null;
  isLoading?: boolean;
  onSelectType?: (type: ArtifactType, id?: string) => void;
}

export function ArtifactOverviewGrid({ availability, isLoading, onSelectType }: ArtifactGridProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <ArtifactCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!availability) {
    return (
      <Card className="p-6 text-center">
        <p className="text-muted-foreground">
          Keep chatting to unlock insights about your journey
        </p>
      </Card>
    );
  }

  const items: { type: ArtifactType; available: boolean; meta?: string; id?: string }[] = [
    {
      type: "relationship",
      available: availability.relationship.available,
      meta: availability.relationship.days_together
        ? `${availability.relationship.days_together} days together`
        : undefined,
    },
    {
      type: "communication",
      available: availability.communication.available,
      meta: availability.communication.message_count
        ? `${availability.communication.message_count} messages analyzed`
        : undefined,
    },
    {
      type: "domain_health",
      available: availability.domain_health.available,
      meta: availability.domain_health.domains?.length
        ? `${availability.domain_health.domains.length} active domains`
        : undefined,
    },
  ];

  // Add thread journeys if available
  if (availability.thread_journey.available && availability.thread_journey.threads) {
    const primaryThread = availability.thread_journey.threads[0];
    items.unshift({
      type: "thread_journey",
      available: true,
      meta: primaryThread.topic,
      id: primaryThread.thread_id,
    });
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {items.map(({ type, available, meta, id }) => {
        const config = ARTIFACT_CONFIG[type];
        const Icon = config.icon;

        return (
          <Card
            key={type}
            className={cn(
              "relative overflow-hidden transition-all",
              available
                ? "cursor-pointer hover:shadow-md hover:border-primary/30"
                : "opacity-60"
            )}
            onClick={() => available && onSelectType?.(type, id)}
          >
            <div className={cn("absolute inset-0 bg-gradient-to-br", config.gradient)} />
            <CardContent className="relative pt-6">
              <div className="flex items-start gap-3">
                <div className={cn(
                  "rounded-lg p-2 shadow-sm",
                  available ? "bg-background/80" : "bg-muted/50"
                )}>
                  <Icon className={cn(
                    "h-5 w-5",
                    available ? "text-primary" : "text-muted-foreground"
                  )} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className={cn(
                    "font-semibold",
                    !available && "text-muted-foreground"
                  )}>
                    {config.title}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {available ? (meta || config.description) : "Keep chatting to unlock"}
                  </p>
                </div>
                {available && (
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
