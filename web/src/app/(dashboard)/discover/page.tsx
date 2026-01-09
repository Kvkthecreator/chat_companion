"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api/client";
import { SeriesDiscoveryCard } from "@/components/series";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ScrollRow } from "@/components/ui/scroll-row";
import type { SeriesSummary } from "@/types";
import { SectionHeader } from "@/components/ui/section-header";
import { BookOpen, Sparkles, Heart, Search, Skull, Drama, Clapperboard, Grid3X3 } from "lucide-react";

// Genre display config with icons
const GENRE_CONFIG: Record<string, { label: string; icon: React.ReactNode }> = {
  // Core Romance
  romance: { label: "Romance", icon: <Heart className="h-5 w-5 text-pink-500" /> },
  dark_romance: { label: "Dark Romance", icon: <Heart className="h-5 w-5 text-rose-700" /> },
  romantic_tension: { label: "Romantic Tension", icon: <Heart className="h-5 w-5 text-red-400" /> },
  enemies_to_lovers: { label: "Enemies to Lovers", icon: <Heart className="h-5 w-5 text-orange-500" /> },
  fake_dating: { label: "Fake Dating", icon: <Heart className="h-5 w-5 text-amber-500" /> },
  // BL/GL
  bl: { label: "Boys Love", icon: <Heart className="h-5 w-5 text-sky-500" /> },
  gl: { label: "Girls Love", icon: <Heart className="h-5 w-5 text-fuchsia-500" /> },
  // Thrillers & Mystery
  mystery: { label: "Mystery", icon: <Search className="h-5 w-5 text-indigo-500" /> },
  survival_thriller: { label: "Survival Thriller", icon: <Skull className="h-5 w-5 text-slate-500" /> },
  psychological: { label: "Psychological", icon: <Skull className="h-5 w-5 text-zinc-600" /> },
  // Settings & Aesthetics
  historical: { label: "Historical", icon: <BookOpen className="h-5 w-5 text-amber-700" /> },
  workplace: { label: "Workplace", icon: <Clapperboard className="h-5 w-5 text-slate-600" /> },
  cozy: { label: "Cozy", icon: <Sparkles className="h-5 w-5 text-amber-400" /> },
  slice_of_life: { label: "Slice of Life", icon: <Clapperboard className="h-5 w-5 text-green-500" /> },
  // Fantasy & Action
  fantasy_action: { label: "Fantasy Action", icon: <Sparkles className="h-5 w-5 text-purple-500" /> },
  otome_isekai: { label: "Otome Isekai", icon: <Sparkles className="h-5 w-5 text-violet-500" /> },
  // Asian Media Aesthetics
  ai_shoujo: { label: "AI Shoujo", icon: <Sparkles className="h-5 w-5 text-cyan-500" /> },
  shoujo: { label: "Shoujo", icon: <Heart className="h-5 w-5 text-pink-400" /> },
  // General
  drama: { label: "Drama", icon: <Drama className="h-5 w-5 text-blue-500" /> },
};

// Priority order for genre rows (most popular/engaging first)
const GENRE_PRIORITY = [
  "romance",
  "romantic_tension",
  "dark_romance",
  "bl",
  "gl",
  "enemies_to_lovers",
  "mystery",
  "psychological",
  "survival_thriller",
  "historical",
  "workplace",
  "cozy",
  "otome_isekai",
  "shoujo",
  "ai_shoujo",
  "fantasy_action",
  "drama",
  "slice_of_life",
  "fake_dating",
];

export default function DiscoverPage() {
  const [series, setSeries] = useState<SeriesSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAllGrid, setShowAllGrid] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        const seriesData = await api.series.list({ status: "active" });
        setSeries(seriesData);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  // Featured series
  const featuredSeries = useMemo(() => {
    return series.find((s) => s.is_featured) || series[0];
  }, [series]);

  // "Start Here" - curated beginner-friendly series (featured + high episode count)
  const startHereSeries = useMemo(() => {
    // Prioritize featured, then by episode count (more content = more polished)
    return series
      .filter((s) => s.id !== featuredSeries?.id)
      .sort((a, b) => {
        if (a.is_featured && !b.is_featured) return -1;
        if (!a.is_featured && b.is_featured) return 1;
        return b.total_episodes - a.total_episodes;
      })
      .slice(0, 6);
  }, [series, featuredSeries]);

  // Group series by genre
  const seriesByGenre = useMemo(() => {
    const grouped: Record<string, SeriesSummary[]> = {};
    series.forEach((s) => {
      if (s.genre) {
        if (!grouped[s.genre]) grouped[s.genre] = [];
        grouped[s.genre].push(s);
      }
    });
    return grouped;
  }, [series]);

  // Get sorted genre keys based on priority and availability
  const sortedGenres = useMemo(() => {
    const available = Object.keys(seriesByGenre);
    return GENRE_PRIORITY.filter((g) => available.includes(g) && seriesByGenre[g].length >= 2);
  }, [seriesByGenre]);

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-48 w-full max-w-2xl rounded-xl" />
        <div className="space-y-3">
          <Skeleton className="h-6 w-32" />
          <div className="flex gap-3">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-40 w-64 flex-shrink-0 rounded-xl" />
            ))}
          </div>
        </div>
        <div className="space-y-3">
          <Skeleton className="h-6 w-32" />
          <div className="flex gap-3">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-40 w-64 flex-shrink-0 rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-10 pb-8">
      {/* Header */}
      <SectionHeader
        title="Discover Stories"
        description="Explore series by genre and find your next adventure."
      />

      {/* Featured Series - Large Hero Card */}
      {featuredSeries && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Featured</h2>
          </div>
          <SeriesDiscoveryCard
            series={featuredSeries}
            featured
            className="max-w-2xl"
          />
        </section>
      )}

      {/* Start Here Row - Curated for new users */}
      {startHereSeries.length > 0 && (
        <ScrollRow
          title="Start Here"
          icon={<BookOpen className="h-5 w-5 text-emerald-500" />}
        >
          {startHereSeries.map((s) => (
            <div key={s.id} className="flex-shrink-0 snap-start w-[260px] sm:w-[280px]">
              <SeriesDiscoveryCard series={s} />
            </div>
          ))}
        </ScrollRow>
      )}

      {/* Genre Rows */}
      {sortedGenres.map((genre) => {
        const config = GENRE_CONFIG[genre] || { label: genre, icon: <BookOpen className="h-5 w-5" /> };
        const genreSeries = seriesByGenre[genre];

        return (
          <ScrollRow
            key={genre}
            title={config.label}
            icon={config.icon}
          >
            {genreSeries.map((s) => (
              <div key={s.id} className="flex-shrink-0 snap-start w-[260px] sm:w-[280px]">
                <SeriesDiscoveryCard series={s} />
              </div>
            ))}
          </ScrollRow>
        );
      })}

      {/* All Series Toggle */}
      <section className="space-y-4">
        <Button
          variant="outline"
          className="w-full justify-center gap-2"
          onClick={() => setShowAllGrid(!showAllGrid)}
        >
          <Grid3X3 className="h-4 w-4" />
          {showAllGrid ? "Hide All Series" : `Browse All ${series.length} Series`}
        </Button>

        {/* All Series Grid (collapsed by default) */}
        {showAllGrid && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {series.map((s) => (
              <SeriesDiscoveryCard key={s.id} series={s} />
            ))}
          </div>
        )}
      </section>

      {/* Empty state */}
      {series.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <BookOpen className="h-8 w-8 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground">No content available yet</p>
        </div>
      )}
    </div>
  );
}
