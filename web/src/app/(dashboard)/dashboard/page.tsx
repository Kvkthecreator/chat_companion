"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, User, Conversation, ArtifactAvailability, Artifact, ArtifactType } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ArtifactOverviewGrid } from "@/components/artifacts";
import { ArtifactDetail } from "@/components/artifacts";
import {
  MessageCircle,
  Target,
  Calendar,
  ChevronRight,
  ArrowLeft,
  Sparkles,
  MapPin,
  Heart,
  Briefcase,
  Activity,
  BookOpen,
  Users,
  Clock,
  Settings,
} from "lucide-react";

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

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [availability, setAvailability] = useState<ArtifactAvailability | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingAvailability, setIsLoadingAvailability] = useState(true);

  // Artifact detail view state
  const [selectedArtifact, setSelectedArtifact] = useState<{
    type: ArtifactType;
    id?: string;
  } | null>(null);
  const [artifactData, setArtifactData] = useState<Artifact | null>(null);
  const [isLoadingArtifact, setIsLoadingArtifact] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [userData, conversationsData] = await Promise.all([
          api.users.me(),
          api.conversations.list({ limit: 3 }).catch(() => []),
        ]);
        setUser(userData);
        setConversations(conversationsData);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      }
      setIsLoading(false);
    };

    const loadAvailability = async () => {
      try {
        const data = await api.artifacts.checkAvailability();
        setAvailability(data);
      } catch (err) {
        console.error("Failed to load artifact availability:", err);
      }
      setIsLoadingAvailability(false);
    };

    loadData();
    loadAvailability();
  }, []);

  // Load artifact when selected
  useEffect(() => {
    if (!selectedArtifact) {
      setArtifactData(null);
      return;
    }

    const loadArtifact = async (regenerate: boolean = false) => {
      if (regenerate) {
        setIsRegenerating(true);
      } else {
        setIsLoadingArtifact(true);
      }

      try {
        let data: Artifact;
        switch (selectedArtifact.type) {
          case "thread_journey":
            if (!selectedArtifact.id) throw new Error("Thread ID required");
            data = await api.artifacts.getThreadJourney(selectedArtifact.id, regenerate);
            break;
          case "domain_health":
            const domain = selectedArtifact.id || "career";
            data = await api.artifacts.getDomainHealth(domain, regenerate);
            break;
          case "communication":
            data = await api.artifacts.getCommunicationProfile(regenerate);
            break;
          case "relationship":
            data = await api.artifacts.getRelationshipSummary(regenerate);
            break;
          default:
            throw new Error("Unknown artifact type");
        }
        setArtifactData(data);
      } catch (err) {
        console.error("Failed to load artifact:", err);
      } finally {
        setIsLoadingArtifact(false);
        setIsRegenerating(false);
      }
    };

    loadArtifact();
  }, [selectedArtifact]);

  const handleSelectArtifact = (type: ArtifactType, id?: string) => {
    setSelectedArtifact({ type, id });
  };

  const handleRegenerate = async () => {
    if (!selectedArtifact) return;
    setIsRegenerating(true);

    try {
      let data: Artifact;
      switch (selectedArtifact.type) {
        case "thread_journey":
          if (!selectedArtifact.id) throw new Error("Thread ID required");
          data = await api.artifacts.getThreadJourney(selectedArtifact.id, true);
          break;
        case "domain_health":
          const domain = selectedArtifact.id || "career";
          data = await api.artifacts.getDomainHealth(domain, true);
          break;
        case "communication":
          data = await api.artifacts.getCommunicationProfile(true);
          break;
        case "relationship":
          data = await api.artifacts.getRelationshipSummary(true);
          break;
        default:
          throw new Error("Unknown artifact type");
      }
      setArtifactData(data);
    } catch (err) {
      console.error("Failed to regenerate artifact:", err);
    } finally {
      setIsRegenerating(false);
    }
  };

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Failed to load user data</div>
      </div>
    );
  }

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  // Show artifact detail view
  if (selectedArtifact) {
    return (
      <div className="mx-auto max-w-3xl pb-20 md:pb-0">
        <ArtifactDetail
          artifact={artifactData}
          isLoading={isLoadingArtifact}
          onBack={() => setSelectedArtifact(null)}
          onRegenerate={handleRegenerate}
          isRegenerating={isRegenerating}
        />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl pb-20 md:pb-0">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">
          {getGreeting()}, {user.display_name || "there"}
        </h1>
        <p className="text-muted-foreground">
          Here's what I've learned from our conversations
        </p>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3 mb-8">
        <Button onClick={() => router.push("/chat")} className="flex-1">
          <MessageCircle className="h-4 w-4 mr-2" />
          Chat with {user.companion_name || "Companion"}
        </Button>
        <Link href="/memory">
          <Button variant="outline">
            <Target className="h-4 w-4 mr-2" />
            View Memory
          </Button>
        </Link>
      </div>

      {/* Artifacts Section - Main Value */}
      <div className="space-y-4 mb-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Your Journey</h2>
          <p className="text-sm text-muted-foreground">Insights from our conversations</p>
        </div>

        <ArtifactOverviewGrid
          availability={availability}
          isLoading={isLoadingAvailability}
          onSelectType={handleSelectArtifact}
        />
      </div>

      {/* Active Threads Preview */}
      {availability?.thread_journey.available && availability.thread_journey.threads && (
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Target className="h-4 w-4" />
                Active Threads
              </CardTitle>
              <Link href="/memory" className="text-sm text-primary hover:underline flex items-center gap-1">
                See all
                <ChevronRight className="h-3 w-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {availability.thread_journey.threads.slice(0, 5).map((thread) => {
                const Icon = thread.domain ? DOMAIN_ICONS[thread.domain] || Target : Target;
                return (
                  <Button
                    key={thread.thread_id}
                    variant="outline"
                    size="sm"
                    className="h-auto py-1.5 px-3"
                    onClick={() => handleSelectArtifact("thread_journey", thread.thread_id)}
                  >
                    <Icon className="h-3.5 w-3.5 mr-1.5 text-primary" />
                    <span className="truncate max-w-[150px]">{thread.topic}</span>
                  </Button>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Conversations - Compact */}
      {conversations.length > 0 && (
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <MessageCircle className="h-4 w-4" />
                Recent Chats
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {conversations.map((conv) => (
                <Link
                  key={conv.id}
                  href={`/chat/${conv.id}`}
                  className="flex items-center justify-between rounded-lg border border-border p-2.5 transition-colors hover:bg-muted"
                >
                  <div className="text-sm">
                    <span className="font-medium">{formatDate(conv.started_at)}</span>
                    <span className="text-muted-foreground ml-2">
                      {conv.message_count} messages
                    </span>
                  </div>
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Schedule Info - Compact */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-primary/10 p-2">
                <Clock className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium">
                  Daily check-in at {formatTime(user.preferred_message_time || "09:00")}
                </p>
                <p className="text-xs text-muted-foreground">
                  {user.timezone || "America/New_York"}
                </p>
              </div>
            </div>
            <Link href="/companion">
              <Button variant="ghost" size="sm">
                <Settings className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {!user.telegram_user_id && (
            <div className="mt-3 rounded-lg bg-muted/50 p-3 text-xs">
              <p className="text-muted-foreground">
                Connect Telegram to receive daily messages.{" "}
                <Link href="/settings" className="text-primary hover:underline">
                  Connect now
                </Link>
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-20 md:pb-0">
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
      <div className="flex gap-3">
        <Skeleton className="h-10 flex-1" />
        <Skeleton className="h-10 w-32" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
        <Skeleton className="h-32 rounded-xl" />
      </div>
      <Skeleton className="h-24 rounded-xl" />
    </div>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatTime(time: string) {
  const [hours, minutes] = time.split(":");
  const hour = parseInt(hours);
  const ampm = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
}
