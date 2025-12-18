"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api/client";
import { SeriesDiscoveryCard } from "@/components/series";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { SeriesSummary } from "@/types";
import { SectionHeader } from "@/components/ui/section-header";
import { BookOpen, Sparkles } from "lucide-react";

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

export default function DiscoverPage() {
  const [series, setSeries] = useState<SeriesSummary[]>([]);
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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

  // Extract unique genres from series
  const availableGenres = useMemo(() => {
    const genres = new Set<string>();
    series.forEach((s) => {
      if (s.genre) genres.add(s.genre);
    });
    return Array.from(genres).sort();
  }, [series]);

  // Filter by genre
  const filteredSeries = useMemo(() => {
    if (!selectedGenre) return series;
    return series.filter((s) => s.genre === selectedGenre);
  }, [series, selectedGenre]);

  // Featured series (first one or one with is_featured)
  const featuredSeries = filteredSeries.find((s) => s.is_featured) || filteredSeries[0];
  const otherSeries = filteredSeries.filter((s) => s.id !== featuredSeries?.id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-9 w-24 rounded-full" />
          ))}
        </div>
        <Skeleton className="h-48 w-full rounded-xl" />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="aspect-[16/10] rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <SectionHeader
          title="Discover Stories"
          description="Explore series by genre and find your next adventure."
        />
      </div>

      {/* Genre Filter */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedGenre === null ? "default" : "outline"}
          size="sm"
          className="rounded-full"
          onClick={() => setSelectedGenre(null)}
        >
          All Genres
        </Button>
        {availableGenres.map((genre) => (
          <Button
            key={genre}
            variant={selectedGenre === genre ? "default" : "outline"}
            size="sm"
            className={cn("rounded-full", selectedGenre === genre && "bg-primary")}
            onClick={() => setSelectedGenre(genre)}
          >
            {GENRE_LABELS[genre] || genre}
          </Button>
        ))}
      </div>

      {/* Featured Series */}
      {featuredSeries && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold">Featured Series</h2>
          </div>
          <SeriesDiscoveryCard
            series={featuredSeries}
            featured
            className="max-w-2xl"
          />
        </section>
      )}

      {/* Series Grid */}
      {otherSeries.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-muted-foreground" />
            <h2 className="text-lg font-semibold">
              {selectedGenre ? GENRE_LABELS[selectedGenre] || selectedGenre : "All Series"}
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {otherSeries.map((s) => (
              <SeriesDiscoveryCard
                key={s.id}
                series={s}
              />
            ))}
          </div>
        </section>
      )}

      {/* Empty state */}
      {filteredSeries.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <BookOpen className="h-8 w-8 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground mb-2">
            {selectedGenre
              ? `No series in ${GENRE_LABELS[selectedGenre] || selectedGenre} yet`
              : "No content available yet"}
          </p>
          {selectedGenre && (
            <Button variant="outline" size="sm" onClick={() => setSelectedGenre(null)}>
              View all genres
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
