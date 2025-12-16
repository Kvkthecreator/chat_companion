"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api/client";
import { EpisodeDiscoveryCard } from "@/components/episodes";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { EpisodeDiscoveryItem } from "@/types";
import { SectionHeader } from "@/components/ui/section-header";
import { Users } from "lucide-react";

export default function DiscoverPage() {
  const [episodes, setEpisodes] = useState<EpisodeDiscoveryItem[]>([]);
  const [archetypes, setArchetypes] = useState<string[]>([]);
  const [selectedArchetype, setSelectedArchetype] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [episodesData, archetypesData] = await Promise.all([
          api.episodeTemplates.list(),
          api.characters.archetypes(),
        ]);
        setEpisodes(episodesData);
        setArchetypes(archetypesData);
      } catch (err) {
        console.error("Failed to load episodes:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const filteredEpisodes = useMemo(() => {
    return selectedArchetype
      ? episodes.filter((e) => e.character_archetype === selectedArchetype)
      : episodes;
  }, [episodes, selectedArchetype]);

  const entryEpisodes = filteredEpisodes.filter((e) => e.episode_type === "entry");
  const coreEpisodes = filteredEpisodes.filter((e) => e.episode_type === "core");
  const heroEpisode = entryEpisodes[0];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-9 w-20 rounded-full" />
          ))}
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="aspect-[16/10] rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <SectionHeader
          title="Step into a moment"
          description="Start with Episode 0, then dive deeper."
        />
        <Link href="/characters">
          <Button variant="outline" size="sm" className="gap-2">
            <Users className="h-4 w-4" />
            Browse characters
          </Button>
        </Link>
      </div>

      <div className="flex flex-wrap gap-2">
        <Button
          variant={selectedArchetype === null ? "default" : "outline"}
          size="sm"
          className="rounded-full"
          onClick={() => setSelectedArchetype(null)}
        >
          All
        </Button>
        {archetypes.map((archetype) => (
          <Button
            key={archetype}
            variant={selectedArchetype === archetype ? "default" : "outline"}
            size="sm"
            className={cn(
              "rounded-full capitalize",
              selectedArchetype === archetype && "bg-primary"
            )}
            onClick={() => setSelectedArchetype(archetype)}
          >
            {archetype}
          </Button>
        ))}
      </div>

      {heroEpisode && (
        <section className="space-y-3">
          <h3 className="text-lg font-semibold">Featured Episode 0</h3>
          <EpisodeDiscoveryCard episode={heroEpisode} className="shadow-md" />
        </section>
      )}

      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Episode 0 (start here)</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {entryEpisodes.map((episode) => (
            <EpisodeDiscoveryCard key={episode.id} episode={episode} />
          ))}
        </div>
        {entryEpisodes.length === 0 && (
          <p className="text-sm text-muted-foreground">No entry episodes found.</p>
        )}
      </section>

      <section className="space-y-3">
        <h3 className="text-lg font-semibold">Core episodes</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {coreEpisodes.slice(0, 6).map((episode) => (
            <EpisodeDiscoveryCard key={episode.id} episode={episode} />
          ))}
        </div>
        {coreEpisodes.length === 0 && (
          <p className="text-sm text-muted-foreground">More episodes coming soon.</p>
        )}
      </section>
    </div>
  );
}
