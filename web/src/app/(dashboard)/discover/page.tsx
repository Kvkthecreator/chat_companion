"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api/client";
import { SeriesDiscoveryCard } from "@/components/series";
import { EpisodeDiscoveryCard } from "@/components/episodes";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { SeriesSummary, EpisodeDiscoveryItem, World } from "@/types";
import { SectionHeader } from "@/components/ui/section-header";
import { BookOpen, Sparkles } from "lucide-react";

export default function DiscoverPage() {
  const [series, setSeries] = useState<SeriesSummary[]>([]);
  const [episodes, setEpisodes] = useState<EpisodeDiscoveryItem[]>([]);
  const [worlds, setWorlds] = useState<World[]>([]);
  const [selectedWorld, setSelectedWorld] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [seriesData, episodesData, worldsData] = await Promise.all([
          api.series.list({ status: "active" }),
          api.episodeTemplates.list(),
          api.worlds.list(),
        ]);
        setSeries(seriesData);
        setEpisodes(episodesData);
        setWorlds(worldsData);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  // Filter by world
  const filteredSeries = useMemo(() => {
    if (!selectedWorld) return series;
    return series.filter((s) => s.world_id === selectedWorld);
  }, [series, selectedWorld]);

  const filteredEpisodes = useMemo(() => {
    if (!selectedWorld) return episodes;
    return episodes.filter((e) => e.world_id === selectedWorld);
  }, [episodes, selectedWorld]);

  // Featured series (first one or one with is_featured)
  const featuredSeries = filteredSeries.find((s) => s.is_featured) || filteredSeries[0];
  const otherSeries = filteredSeries.filter((s) => s.id !== featuredSeries?.id);

  // Entry episodes for quick start
  const entryEpisodes = filteredEpisodes.filter((e) => e.episode_type === "entry").slice(0, 6);

  // Build world map for lookup
  const worldMap = useMemo(() => new Map(worlds.map((w) => [w.id, w])), [worlds]);

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
          description="Explore series by world, or dive into an episode."
        />
      </div>

      {/* World Filter */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedWorld === null ? "default" : "outline"}
          size="sm"
          className="rounded-full"
          onClick={() => setSelectedWorld(null)}
        >
          All Worlds
        </Button>
        {worlds.map((world) => (
          <Button
            key={world.id}
            variant={selectedWorld === world.id ? "default" : "outline"}
            size="sm"
            className={cn("rounded-full", selectedWorld === world.id && "bg-primary")}
            onClick={() => setSelectedWorld(world.id)}
          >
            {world.name}
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
            world={featuredSeries.world_id ? worldMap.get(featuredSeries.world_id) : undefined}
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
              {selectedWorld ? `Series in ${worldMap.get(selectedWorld)?.name}` : "All Series"}
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {otherSeries.map((s) => (
              <SeriesDiscoveryCard
                key={s.id}
                series={s}
                world={s.world_id ? worldMap.get(s.world_id) : undefined}
              />
            ))}
          </div>
        </section>
      )}

      {/* Quick Start Episodes */}
      {entryEpisodes.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold">Quick Start (Episode 0)</h2>
          <p className="text-sm text-muted-foreground">
            Jump right in—these episodes are perfect entry points.
          </p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {entryEpisodes.map((episode) => (
              <EpisodeDiscoveryCard key={episode.id} episode={episode} />
            ))}
          </div>
        </section>
      )}

      {/* Empty state */}
      {filteredSeries.length === 0 && filteredEpisodes.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
            <BookOpen className="h-8 w-8 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground mb-2">
            {selectedWorld
              ? `No content in ${worldMap.get(selectedWorld)?.name} yet`
              : "No content available yet"}
          </p>
          {selectedWorld && (
            <Button variant="outline" size="sm" onClick={() => setSelectedWorld(null)}>
              View all worlds
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
