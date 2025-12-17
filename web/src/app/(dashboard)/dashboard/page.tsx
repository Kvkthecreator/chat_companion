"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { api } from "@/lib/api/client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Play, Sparkles, BookOpen, ArrowRight } from "lucide-react";
import type { RelationshipWithCharacter, User, SeriesSummary, World } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [relationships, setRelationships] = useState<RelationshipWithCharacter[]>([]);
  const [series, setSeries] = useState<SeriesSummary[]>([]);
  const [worlds, setWorlds] = useState<World[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const supabase = createClient();

  useEffect(() => {
    async function loadData() {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          router.push("/login");
          return;
        }

        // Load data in parallel
        const [userData, relationshipsData, seriesData, worldsData] = await Promise.all([
          api.users.me().catch(() => null),
          api.relationships.list().catch(() => []),
          api.series.list({ status: "active" }).catch(() => []),
          api.worlds.list().catch(() => []),
        ]);

        setUser(userData);
        setRelationships(relationshipsData);
        setSeries(seriesData);
        setWorlds(worldsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load data");
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // Sort relationships by last interaction
  const sortedRelationships = [...relationships].sort((a, b) => {
    const timeA = a.last_interaction_at ? new Date(a.last_interaction_at).getTime() : 0;
    const timeB = b.last_interaction_at ? new Date(b.last_interaction_at).getTime() : 0;
    return timeB - timeA;
  });

  // Hero: most recent relationship with active episode
  const heroRelationship = sortedRelationships[0];

  // Build world map
  const worldMap = new Map(worlds.map((w) => [w.id, w]));

  // Featured series for discovery
  const featuredSeries = series.find((s) => s.is_featured) || series[0];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {user?.display_name ? `Welcome back, ${user.display_name}` : "Welcome back"}
        </h1>
        <p className="text-muted-foreground">
          Continue your stories or discover something new.
        </p>
      </div>

      {error && (
        <Card className="border-destructive/40 bg-destructive/5 p-4">
          <p className="text-destructive font-medium">Unable to load data</p>
          <p className="text-destructive/80 text-sm">{error}</p>
        </Card>
      )}

      {/* Continue Episode - Hero Card */}
      {heroRelationship && (
        <section>
          <h2 className="mb-3 text-lg font-semibold text-muted-foreground flex items-center gap-2">
            <Play className="h-4 w-4" />
            Continue Your Story
          </h2>
          <Link href={`/chat/${heroRelationship.character_id}`}>
            <Card className="overflow-hidden hover:shadow-lg transition-all group cursor-pointer ring-2 ring-primary/20 hover:ring-primary/40">
              <div className="flex flex-col sm:flex-row">
                <div className="relative w-full sm:w-48 h-48 sm:h-auto shrink-0 overflow-hidden bg-muted">
                  {heroRelationship.character_avatar_url ? (
                    <img
                      src={heroRelationship.character_avatar_url}
                      alt={heroRelationship.character_name}
                      className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-primary/20 to-secondary/20">
                      <span className="text-4xl font-bold text-muted-foreground/50">
                        {heroRelationship.character_name[0]}
                      </span>
                    </div>
                  )}
                </div>
                <CardContent className="p-5 flex flex-col justify-between flex-1">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="secondary" className="text-xs">
                        Episode {heroRelationship.total_episodes || 0}
                      </Badge>
                      {heroRelationship.last_interaction_at && (
                        <span className="text-xs text-muted-foreground">
                          {formatRelativeTime(heroRelationship.last_interaction_at)}
                        </span>
                      )}
                    </div>
                    <h3 className="text-xl font-semibold mb-1">{heroRelationship.character_name}</h3>
                    <p className="text-sm text-muted-foreground capitalize mb-2">
                      {heroRelationship.character_archetype}
                    </p>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{heroRelationship.total_messages} messages</span>
                      <span>•</span>
                      <span className="capitalize">{heroRelationship.stage || "acquaintance"}</span>
                    </div>
                  </div>
                  <Button className="mt-4 w-full sm:w-auto gap-2">
                    <Play className="h-4 w-4" />
                    Resume Episode
                  </Button>
                </CardContent>
              </div>
            </Card>
          </Link>
        </section>
      )}

      {/* Your Stories - Grouped by recent activity */}
      {sortedRelationships.length > 1 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-muted-foreground">Your Stories</h2>
            <Link href="/dashboard/chats" className="text-sm text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
            {sortedRelationships.slice(1, 6).map((rel) => (
              <StoryCard key={rel.id} relationship={rel} />
            ))}
          </div>
        </section>
      )}

      {/* Discover New Series */}
      {featuredSeries && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-muted-foreground flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              Discover Something New
            </h2>
            <Link href="/discover" className="text-sm text-primary hover:underline flex items-center gap-1">
              Browse all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <Link href={`/series/${featuredSeries.slug}`}>
            <Card className="overflow-hidden hover:shadow-lg transition-all group cursor-pointer">
              <div className="relative h-40 overflow-hidden">
                {featuredSeries.cover_image_url ? (
                  <img
                    src={featuredSeries.cover_image_url}
                    alt={featuredSeries.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-blue-600/40 via-purple-500/30 to-pink-500/20" />
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-4">
                  <div className="flex items-center gap-2 mb-2">
                    {featuredSeries.world_id && worldMap.get(featuredSeries.world_id) && (
                      <Badge variant="secondary" className="bg-black/60 text-white border-0 text-[10px]">
                        {worldMap.get(featuredSeries.world_id)?.name}
                      </Badge>
                    )}
                    <Badge variant="secondary" className="bg-primary/80 text-primary-foreground text-[10px] capitalize">
                      {featuredSeries.series_type}
                    </Badge>
                  </div>
                  <h3 className="font-semibold text-white text-lg">{featuredSeries.title}</h3>
                  {featuredSeries.tagline && (
                    <p className="text-white/80 text-sm italic mt-1">{featuredSeries.tagline}</p>
                  )}
                  <div className="flex items-center gap-2 text-white/70 text-xs mt-2">
                    <BookOpen className="h-3 w-3" />
                    <span>{featuredSeries.total_episodes} episodes</span>
                  </div>
                </div>
              </div>
            </Card>
          </Link>
        </section>
      )}

      {/* Empty state - no relationships yet */}
      {relationships.length === 0 && (
        <Card className="py-12">
          <CardContent className="flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white text-2xl mb-4">
              <Sparkles className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Start Your First Story</h3>
            <p className="text-sm text-muted-foreground max-w-sm mb-4">
              Discover series and characters waiting to meet you.
            </p>
            <Button asChild>
              <Link href="/discover">Discover Stories</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface StoryCardProps {
  relationship: RelationshipWithCharacter;
}

function StoryCard({ relationship }: StoryCardProps) {
  return (
    <Link href={`/chat/${relationship.character_id}`}>
      <Card className="overflow-hidden hover:shadow-md transition-all duration-200 hover:-translate-y-0.5 cursor-pointer group h-full">
        <div className="aspect-[3/4] relative overflow-hidden bg-muted">
          {relationship.character_avatar_url ? (
            <img
              src={relationship.character_avatar_url}
              alt={relationship.character_name}
              className="w-full h-full object-cover object-top group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-muted to-muted-foreground/20">
              <span className="text-3xl font-bold text-muted-foreground/50">
                {relationship.character_name[0]}
              </span>
            </div>
          )}

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />

          {/* Episode badge */}
          <Badge
            variant="secondary"
            className="absolute top-2 right-2 bg-black/60 text-white border-0 text-[10px]"
          >
            Ep {relationship.total_episodes || 0}
          </Badge>

          {/* Name overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-2 text-white">
            <h3 className="font-semibold text-sm leading-tight drop-shadow-md truncate">
              {relationship.character_name}
            </h3>
            <p className="text-[11px] text-white/75">
              {relationship.last_interaction_at
                ? formatRelativeTime(relationship.last_interaction_at)
                : "Start episode"}
            </p>
          </div>
        </div>
      </Card>
    </Link>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
      {/* Hero skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
      {/* Grid skeleton */}
      <div className="space-y-4">
        <Skeleton className="h-5 w-32" />
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          {[...Array(5)].map((_, i) => (
            <Skeleton key={i} className="aspect-[3/4] rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}
