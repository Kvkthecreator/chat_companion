"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  MapPin,
  Heart,
  MessageSquare,
  Users,
  Briefcase,
  Sparkles,
  Activity,
  BookOpen,
  RefreshCw,
  Quote,
  Calendar,
  TrendingUp,
  Clock,
  ArrowLeft,
  CheckCircle,
  Circle,
  AlertCircle,
} from "lucide-react";
import type { Artifact, ArtifactSection } from "@/lib/api/client";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

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

interface ArtifactDetailProps {
  artifact: Artifact | null;
  isLoading?: boolean;
  error?: Error | null;
  onBack?: () => void;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
}

export function ArtifactDetail({
  artifact,
  isLoading,
  error,
  onBack,
  onRegenerate,
  isRegenerating,
}: ArtifactDetailProps) {
  if (isLoading) {
    return <ArtifactDetailSkeleton onBack={onBack} />;
  }

  if (error) {
    return (
      <div className="space-y-4">
        {onBack && (
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        )}
        <Card className="border-destructive/50">
          <CardContent className="pt-6 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="text-muted-foreground">Failed to load artifact</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!artifact) {
    return (
      <div className="space-y-4">
        {onBack && (
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        )}
        <Card>
          <CardContent className="pt-6 text-center text-muted-foreground">
            No artifact data available
          </CardContent>
        </Card>
      </div>
    );
  }

  // Not enough data state
  if (!artifact.is_meaningful) {
    return (
      <div className="space-y-4">
        {onBack && (
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        )}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">{artifact.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-muted/50 rounded-lg p-4 text-center">
              <p className="text-muted-foreground">
                {artifact.min_data_reason || "Not enough data to generate this artifact yet."}
              </p>
              <p className="text-sm text-muted-foreground/70 mt-2">
                Keep chatting and I'll learn more about you!
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const DomainIcon = artifact.domain ? DOMAIN_ICONS[artifact.domain] || MessageSquare : MessageSquare;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        {onBack && (
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        )}
        <div className="flex items-center gap-2 ml-auto">
          {artifact.generated_at && (
            <span className="text-xs text-muted-foreground">
              Updated {formatDistanceToNow(new Date(artifact.generated_at), { addSuffix: true })}
            </span>
          )}
          {onRegenerate && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRegenerate}
              disabled={isRegenerating}
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", isRegenerating && "animate-spin")} />
              Regenerate
            </Button>
          )}
        </div>
      </div>

      {/* Title Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <DomainIcon className="h-5 w-5 text-primary" />
            </div>
            <div className="flex-1">
              <CardTitle className="text-xl">{artifact.title}</CardTitle>
              {artifact.domain && (
                <Badge variant="secondary" className="mt-2 capitalize">
                  {artifact.domain.replace(/_/g, " ")}
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>

        {/* Companion Voice */}
        {artifact.companion_voice && (
          <CardContent className="pt-0">
            <div className="bg-muted/50 rounded-lg p-4 border-l-4 border-primary/30">
              <div className="flex gap-2">
                <Quote className="h-4 w-4 text-primary/50 shrink-0 mt-0.5" />
                <p className="text-sm italic text-foreground/90">
                  {artifact.companion_voice}
                </p>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Sections */}
      {artifact.sections.map((section, index) => (
        <SectionRenderer key={index} section={section} />
      ))}

      {/* Data Sources Footer */}
      {artifact.data_sources.length > 0 && (
        <div className="text-xs text-muted-foreground pt-4 border-t">
          <span className="font-medium">Sources: </span>
          {artifact.data_sources.join(", ")}
        </div>
      )}
    </div>
  );
}

function SectionRenderer({ section }: { section: ArtifactSection }) {
  switch (section.type) {
    case "timeline":
      return <TimelineSection content={section.content as TimelineContent} />;
    case "stats":
      return <StatsSection content={section.content as StatsContent} />;
    case "list":
      return <ListSection content={section.content as ListContent} />;
    case "text":
      return <TextSection content={section.content as TextContent} />;
    case "milestones":
      return <MilestonesSection content={section.content as MilestonesContent} />;
    case "domains":
      return <DomainsSection content={section.content as DomainsContent} />;
    case "traits":
      return <TraitsSection content={section.content as TraitsContent} />;
    case "people":
      return <PeopleSection content={section.content as PeopleContent} />;
    default:
      return <GenericSection content={section.content} />;
  }
}

// Section content types
interface TimelineContent {
  title?: string;
  events: Array<{
    date: string;
    description: string;
    type?: string;
  }>;
}

interface StatsContent {
  title?: string;
  items: Array<{
    label: string;
    value: string | number;
    icon?: string;
  }>;
}

interface ListContent {
  title?: string;
  items: string[];
}

interface TextContent {
  title?: string;
  text: string;
}

interface MilestonesContent {
  title?: string;
  milestones: Array<{
    title: string;
    description?: string;
    achieved: boolean;
    date?: string;
  }>;
}

interface DomainsContent {
  title?: string;
  domains: Array<{
    name: string;
    activity_level: "high" | "medium" | "low" | "inactive";
    thread_count: number;
    recent_topics?: string[];
  }>;
}

interface TraitsContent {
  title?: string;
  traits: Array<{
    trait: string;
    description: string;
    examples?: string[];
  }>;
}

interface PeopleContent {
  title?: string;
  people: Array<{
    name: string;
    relationship?: string;
    context?: string;
    mention_count?: number;
  }>;
}

function TimelineSection({ content }: { content: TimelineContent }) {
  return (
    <Card>
      {content.title && (
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            {content.title}
          </CardTitle>
        </CardHeader>
      )}
      <CardContent className={content.title ? "pt-0" : "pt-6"}>
        <div className="relative pl-6 space-y-4">
          <div className="absolute left-2 top-2 bottom-2 w-px bg-border" />
          {content.events.map((event, i) => (
            <div key={i} className="relative">
              <div className="absolute -left-4 top-1.5 h-2 w-2 rounded-full bg-primary" />
              <div className="space-y-1">
                <span className="text-xs text-muted-foreground">{event.date}</span>
                <p className="text-sm">{event.description}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function StatsSection({ content }: { content: StatsContent }) {
  return (
    <Card>
      {content.title && (
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            {content.title}
          </CardTitle>
        </CardHeader>
      )}
      <CardContent className={content.title ? "pt-0" : "pt-6"}>
        <div className="grid grid-cols-2 gap-4">
          {content.items.map((item, i) => (
            <div key={i} className="text-center p-3 bg-muted/30 rounded-lg">
              <p className="text-2xl font-bold text-primary">{item.value}</p>
              <p className="text-xs text-muted-foreground">{item.label}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function ListSection({ content }: { content: ListContent }) {
  return (
    <Card>
      {content.title && (
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{content.title}</CardTitle>
        </CardHeader>
      )}
      <CardContent className={content.title ? "pt-0" : "pt-6"}>
        <ul className="space-y-2">
          {content.items.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function TextSection({ content }: { content: TextContent }) {
  return (
    <Card>
      {content.title && (
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{content.title}</CardTitle>
        </CardHeader>
      )}
      <CardContent className={content.title ? "pt-0" : "pt-6"}>
        <p className="text-sm text-muted-foreground leading-relaxed">{content.text}</p>
      </CardContent>
    </Card>
  );
}

function MilestonesSection({ content }: { content: MilestonesContent }) {
  return (
    <Card>
      {content.title && (
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{content.title}</CardTitle>
        </CardHeader>
      )}
      <CardContent className={content.title ? "pt-0" : "pt-6"}>
        <div className="space-y-3">
          {content.milestones.map((milestone, i) => (
            <div key={i} className="flex items-start gap-3">
              {milestone.achieved ? (
                <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
              ) : (
                <Circle className="h-5 w-5 text-muted-foreground shrink-0 mt-0.5" />
              )}
              <div>
                <p className={cn("font-medium text-sm", !milestone.achieved && "text-muted-foreground")}>
                  {milestone.title}
                </p>
                {milestone.description && (
                  <p className="text-xs text-muted-foreground">{milestone.description}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function DomainsSection({ content }: { content: DomainsContent }) {
  const activityColors: Record<string, string> = {
    high: "bg-green-500",
    medium: "bg-yellow-500",
    low: "bg-orange-500",
    inactive: "bg-muted",
  };

  return (
    <Card>
      {content.title && (
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{content.title}</CardTitle>
        </CardHeader>
      )}
      <CardContent className={content.title ? "pt-0" : "pt-6"}>
        <div className="space-y-4">
          {content.domains.map((domain, i) => {
            const Icon = DOMAIN_ICONS[domain.name] || Activity;
            return (
              <div key={i} className="flex items-start gap-3">
                <div className="rounded-lg bg-muted/50 p-2">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm capitalize">{domain.name.replace(/_/g, " ")}</span>
                    <div className={cn("h-2 w-2 rounded-full", activityColors[domain.activity_level])} />
                    <span className="text-xs text-muted-foreground">
                      {domain.thread_count} thread{domain.thread_count !== 1 ? "s" : ""}
                    </span>
                  </div>
                  {domain.recent_topics && domain.recent_topics.length > 0 && (
                    <p className="text-xs text-muted-foreground mt-1 truncate">
                      {domain.recent_topics.join(", ")}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function TraitsSection({ content }: { content: TraitsContent }) {
  return (
    <Card>
      {content.title && (
        <CardHeader className="pb-3">
          <CardTitle className="text-base">{content.title}</CardTitle>
        </CardHeader>
      )}
      <CardContent className={content.title ? "pt-0" : "pt-6"}>
        <div className="space-y-4">
          {content.traits.map((trait, i) => (
            <div key={i}>
              <p className="font-medium text-sm">{trait.trait}</p>
              <p className="text-sm text-muted-foreground">{trait.description}</p>
              {trait.examples && trait.examples.length > 0 && (
                <p className="text-xs text-muted-foreground/70 mt-1 italic">
                  e.g., {trait.examples.join(", ")}
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function PeopleSection({ content }: { content: PeopleContent }) {
  return (
    <Card>
      {content.title && (
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Users className="h-4 w-4" />
            {content.title}
          </CardTitle>
        </CardHeader>
      )}
      <CardContent className={content.title ? "pt-0" : "pt-6"}>
        <div className="space-y-3">
          {content.people.map((person, i) => (
            <div key={i} className="flex items-start gap-3">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-sm font-medium text-primary">
                  {person.name.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm">{person.name}</span>
                  {person.relationship && (
                    <Badge variant="outline" className="text-xs">
                      {person.relationship}
                    </Badge>
                  )}
                </div>
                {person.context && (
                  <p className="text-xs text-muted-foreground">{person.context}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function GenericSection({ content }: { content: unknown }) {
  if (typeof content === "string") {
    return <TextSection content={{ text: content }} />;
  }
  return null;
}

function ArtifactDetailSkeleton({ onBack }: { onBack?: () => void }) {
  return (
    <div className="space-y-4">
      {onBack && (
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
      )}
      <Card>
        <CardHeader>
          <div className="flex items-start gap-3">
            <Skeleton className="h-9 w-9 rounded-lg" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-5 w-20" />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-20 w-full rounded-lg" />
        </CardContent>
      </Card>
      <Skeleton className="h-40 w-full rounded-xl" />
      <Skeleton className="h-32 w-full rounded-xl" />
    </div>
  );
}
