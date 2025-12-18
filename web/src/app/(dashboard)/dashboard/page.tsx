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
import { ScrollRow } from "@/components/ui/scroll-row";
import { SeriesDiscoveryCard, ContinueWatchingCard } from "@/components/series";
import { cn } from "@/lib/utils";
import { Play, Sparkles, BookOpen } from "lucide-react";
import type { User, SeriesSummary, ContinueWatchingItem } from "@/types";

// Genre display labels
const GENRE_LABELS: Record<string, string> = {
  slice_of_life: "Slice of Life",
  romance: "Romance",
  drama: "Drama",
  comedy: "Comedy",
  fantasy: "Fantasy",
  mystery: "Mystery",
  thriller: "Thriller",
  sci_fi: "Sci-Fi",
  horror: "Horror",
  action: "Action",
};

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [continueWatching, setContinueWatching] = useState<ContinueWatchingItem[]>([]);
  const [discoverSeries, setDiscoverSeries] = useState<SeriesSummary[]>([]);
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
        const [userData, continueData, seriesData] = await Promise.all([
          api.users.me().catch(() => null),
          api.series.getContinueWatching(10).catch(() => ({ items: [] })),
          api.series.list({ status: "active" }).catch(() => []),
        ]);

        setUser(userData);
        setContinueWatching(continueData.items);

        // For discover: filter out series user has already started
        const startedSeriesIds = new Set(continueData.items.map(item => item.series_id));
        const notStarted = seriesData.filter(s => !startedSeriesIds.has(s.id));
        setDiscoverSeries(notStarted);
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

  // Hero: most recent continue watching item
  const heroItem = continueWatching[0];
  const otherContinueWatching = continueWatching.slice(1);

  // Featured series for new users
  const featuredSeries = discoverSeries.find(s => s.is_featured) || discoverSeries[0];

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {user?.display_name ? `Welcome back, ${user.display_name}` : "Welcome back"}
        </h1>
        <p className="text-muted-foreground">
          {continueWatching.length > 0
            ? "Continue your stories or discover something new."
            : "Start your first story adventure."}
        </p>
      </div>

      {error && (
        <Card className="border-destructive/40 bg-destructive/5 p-4">
          <p className="text-destructive font-medium">Unable to load data</p>
          <p className="text-destructive/80 text-sm">{error}</p>
        </Card>
      )}

      {/* Hero Section - Resume Most Recent */}
      {heroItem && (
        <HeroCard item={heroItem} />
      )}

      {/* Continue Watching Row */}
      {otherContinueWatching.length > 0 && (
        <ScrollRow
          title="Continue Watching"
          icon={<Play className="h-5 w-5 text-primary" />}
        >
          {otherContinueWatching.map((item) => (
            <ContinueWatchingCard key={item.series_id} item={item} />
          ))}
        </ScrollRow>
      )}

      {/* Discover New Series Row */}
      {discoverSeries.length > 0 && (
        <ScrollRow
          title="Discover New Stories"
          icon={<Sparkles className="h-5 w-5 text-primary" />}
        >
          {discoverSeries.slice(0, 10).map((series) => (
            <div key={series.id} className="flex-shrink-0 snap-start w-[280px] sm:w-[320px]">
              <SeriesDiscoveryCard series={series} />
            </div>
          ))}
          {/* "See All" card */}
          <Link
            href="/discover"
            className="flex-shrink-0 snap-start w-[280px] sm:w-[320px]"
          >
            <Card className="h-full aspect-[16/10] flex items-center justify-center bg-muted/50 hover:bg-muted transition-colors cursor-pointer group">
              <div className="text-center">
                <BookOpen className="h-8 w-8 mx-auto mb-2 text-muted-foreground group-hover:text-primary transition-colors" />
                <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
                  Browse All Stories
                </span>
              </div>
            </Card>
          </Link>
        </ScrollRow>
      )}

      {/* Empty state - no activity at all */}
      {continueWatching.length === 0 && discoverSeries.length === 0 && (
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

      {/* New user with no activity but series available */}
      {continueWatching.length === 0 && featuredSeries && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Start Here</h2>
          </div>
          <div className="max-w-2xl">
            <SeriesDiscoveryCard series={featuredSeries} featured />
          </div>
        </section>
      )}
    </div>
  );
}

/**
 * Hero card for the most recent continue watching item
 */
function HeroCard({ item }: { item: ContinueWatchingItem }) {
  const genreLabel = item.series_genre ? (GENRE_LABELS[item.series_genre] || item.series_genre) : null;

  return (
    <Link href={`/chat/${item.character_id}?episode=${item.current_episode_id}`}>
      <Card className="overflow-hidden hover:shadow-lg transition-all group cursor-pointer ring-2 ring-primary/20 hover:ring-primary/40">
        <div className="relative h-48 sm:h-64 overflow-hidden">
          {item.series_cover_image_url ? (
            <img
              src={item.series_cover_image_url}
              alt={item.series_title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-blue-600/40 via-purple-500/30 to-pink-500/20" />
          )}

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent" />

          {/* Play button overlay */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="h-20 w-20 rounded-full bg-white/95 flex items-center justify-center shadow-2xl">
              <Play className="h-10 w-10 text-primary ml-1" fill="currentColor" />
            </div>
          </div>

          {/* Progress bar */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
            <div
              className="h-full bg-primary"
              style={{ width: `${Math.min((item.current_episode_number / item.total_episodes) * 100, 100)}%` }}
            />
          </div>

          {/* Content */}
          <div className="absolute bottom-0 left-0 right-0 p-5">
            <div className="flex items-center gap-2 mb-2">
              {genreLabel && (
                <Badge variant="secondary" className="bg-primary/80 text-primary-foreground text-xs">
                  {genreLabel}
                </Badge>
              )}
              <Badge variant="secondary" className="bg-black/60 text-white border-0 text-xs">
                Episode {item.current_episode_number} of {item.total_episodes}
              </Badge>
            </div>
            <h2 className="text-2xl font-bold text-white mb-1 drop-shadow-lg">
              {item.series_title}
            </h2>
            <p className="text-white/80 text-sm">
              Continue: {item.current_episode_title}
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
      <Skeleton className="h-48 sm:h-64 w-full rounded-xl" />
      {/* Row skeleton */}
      <div className="space-y-3">
        <Skeleton className="h-5 w-32" />
        <div className="flex gap-3 overflow-hidden">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="flex-shrink-0 w-[280px] sm:w-[320px] aspect-[16/9] rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}
