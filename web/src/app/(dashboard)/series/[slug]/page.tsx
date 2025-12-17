"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api/client";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { Play, ArrowLeft, BookOpen } from "lucide-react";
import type { SeriesWithEpisodes, World } from "@/types";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default function SeriesPage({ params }: PageProps) {
  const { slug } = use(params);
  const router = useRouter();
  const [series, setSeries] = useState<SeriesWithEpisodes | null>(null);
  const [world, setWorld] = useState<World | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [startingEpisode, setStartingEpisode] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        // Fetch series with episodes - need to find by slug first
        // For now, list and filter (TODO: add getBySlug endpoint)
        const allSeries = await api.series.list({ status: "active" });
        const found = allSeries.find((s) => s.slug === slug);

        if (found) {
          const seriesData = await api.series.getWithEpisodes(found.id);
          setSeries(seriesData);

          // Fetch world if set
          if (seriesData.world_id) {
            try {
              const worldData = await api.worlds.get(seriesData.world_id);
              setWorld(worldData);
            } catch {
              // World may not exist
            }
          }
        }
      } catch (err) {
        console.error("Failed to load series:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [slug]);

  const handleStartEpisode = async (episodeId: string, characterId: string | null) => {
    if (startingEpisode || !characterId) return;
    setStartingEpisode(episodeId);

    try {
      // Ensure engagement exists
      await api.relationships.create(characterId).catch(() => {});
      router.push(`/chat/${characterId}?episode=${episodeId}`);
    } catch (err) {
      console.error("Failed to start episode:", err);
      setStartingEpisode(null);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full rounded-xl" />
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!series) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-muted-foreground mb-4">Series not found</p>
        <Button asChild variant="outline">
          <Link href="/discover">Back to Discover</Link>
        </Button>
      </div>
    );
  }

  // Find the entry episode (Episode 0 or default)
  const entryEpisode = series.episodes.find((e) => e.is_default) || series.episodes[0];
  const otherEpisodes = series.episodes.filter((e) => e.id !== entryEpisode?.id);

  return (
    <div className="space-y-8">
      {/* Back navigation */}
      <Link
        href="/discover"
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Discover
      </Link>

      {/* Hero section */}
      <div className="relative overflow-hidden rounded-xl">
        {series.cover_image_url ? (
          <img
            src={series.cover_image_url}
            alt={series.title}
            className="w-full h-64 object-cover"
          />
        ) : (
          <div className="w-full h-64 bg-gradient-to-br from-blue-600/40 via-purple-500/30 to-pink-500/20" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent" />

        <div className="absolute bottom-0 left-0 right-0 p-6">
          <div className="flex flex-wrap gap-2 mb-3">
            {world && (
              <Badge variant="secondary" className="bg-background/80">
                {world.name}
              </Badge>
            )}
            <Badge variant="secondary" className="bg-primary/80 text-primary-foreground capitalize">
              {series.series_type}
            </Badge>
            {series.genre && (
              <Badge variant="outline" className="bg-background/80 capitalize">
                {series.genre.replace("_", " ")}
              </Badge>
            )}
          </div>

          <h1 className="text-3xl font-bold mb-2">{series.title}</h1>

          {series.tagline && (
            <p className="text-lg text-muted-foreground italic mb-4">{series.tagline}</p>
          )}

          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-1">
              <BookOpen className="h-4 w-4" />
              {series.episodes.length} episode{series.episodes.length !== 1 ? "s" : ""}
            </div>
          </div>
        </div>
      </div>

      {/* Description */}
      {series.description && (
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p>{series.description}</p>
        </div>
      )}

      {/* Entry Episode - Featured */}
      {entryEpisode && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">Start Here</h2>
          <Card
            className={cn(
              "overflow-hidden cursor-pointer transition-all duration-200",
              "hover:shadow-xl hover:-translate-y-1 hover:ring-2 hover:ring-primary/50",
              "group",
              startingEpisode === entryEpisode.id && "pointer-events-none opacity-80"
            )}
            onClick={() => handleStartEpisode(entryEpisode.id, entryEpisode.character_id)}
          >
            <div className="flex flex-col sm:flex-row">
              <div className="relative w-full sm:w-64 h-40 sm:h-auto shrink-0 overflow-hidden bg-muted">
                {entryEpisode.background_image_url ? (
                  <img
                    src={entryEpisode.background_image_url}
                    alt={entryEpisode.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                ) : (
                  <div className="w-full h-full bg-gradient-to-br from-primary/30 to-accent/20" />
                )}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="h-12 w-12 rounded-full bg-white/95 flex items-center justify-center shadow-lg">
                    <Play className="h-5 w-5 text-primary ml-0.5" fill="currentColor" />
                  </div>
                </div>
              </div>
              <CardContent className="p-5 flex-1">
                <Badge variant="secondary" className="mb-2">
                  Episode {entryEpisode.episode_number}
                </Badge>
                <h3 className="text-lg font-semibold mb-2">{entryEpisode.title}</h3>
                <p className="text-sm text-muted-foreground">
                  Begin your journey with {series.title}
                </p>
                <Button className="mt-4 gap-2" disabled={!!startingEpisode}>
                  <Play className="h-4 w-4" />
                  {startingEpisode === entryEpisode.id ? "Starting..." : "Start Episode"}
                </Button>
              </CardContent>
            </div>
          </Card>
        </section>
      )}

      {/* Other Episodes */}
      {otherEpisodes.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">More Episodes</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {otherEpisodes.map((episode) => (
              <Card
                key={episode.id}
                className={cn(
                  "overflow-hidden cursor-pointer transition-all duration-200",
                  "hover:shadow-lg hover:-translate-y-0.5 hover:ring-1 hover:ring-primary/30",
                  "group",
                  startingEpisode === episode.id && "pointer-events-none opacity-80"
                )}
                onClick={() => handleStartEpisode(episode.id, episode.character_id)}
              >
                <div className="aspect-[16/9] relative overflow-hidden bg-muted">
                  {episode.background_image_url ? (
                    <img
                      src={episode.background_image_url}
                      alt={episode.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-muted to-muted-foreground/10" />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                  <div className="absolute bottom-0 left-0 right-0 p-3">
                    <Badge variant="secondary" className="bg-black/60 text-white border-0 text-[10px] mb-1">
                      Episode {episode.episode_number}
                    </Badge>
                    <h4 className="font-medium text-white text-sm line-clamp-1">{episode.title}</h4>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
