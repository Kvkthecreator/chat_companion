"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Play } from "lucide-react";
import type { ContinueWatchingItem } from "@/types";

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

interface ContinueWatchingCardProps {
  item: ContinueWatchingItem;
  className?: string;
}

/**
 * Card for "Continue Watching" row.
 * Links directly to chat with the current episode.
 */
export function ContinueWatchingCard({ item, className }: ContinueWatchingCardProps) {
  const genreLabel = item.series_genre ? (GENRE_LABELS[item.series_genre] || item.series_genre) : null;

  return (
    <Link href={`/chat/${item.character_id}?episode=${item.current_episode_id}`}>
      <Card
        className={cn(
          "relative overflow-hidden cursor-pointer transition-all duration-200",
          "hover:shadow-xl hover:-translate-y-1 hover:ring-2 hover:ring-primary/50",
          "group flex-shrink-0 snap-start",
          "w-[280px] sm:w-[320px]",
          className
        )}
      >
        {/* Cover image */}
        <div className="aspect-[16/9] relative overflow-hidden">
          {item.series_cover_image_url ? (
            <img
              src={item.series_cover_image_url}
              alt={item.series_title}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-blue-600/40 via-purple-500/30 to-pink-500/20" />
          )}

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/50 to-transparent" />

          {/* Play indicator on hover */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="h-14 w-14 rounded-full bg-white/95 flex items-center justify-center shadow-xl">
              <Play className="h-6 w-6 text-primary ml-0.5" fill="currentColor" />
            </div>
          </div>

          {/* Progress bar */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
            <div
              className="h-full bg-primary"
              style={{ width: `${Math.min((item.current_episode_number / item.total_episodes) * 100, 100)}%` }}
            />
          </div>

          {/* Genre badge */}
          {genreLabel && (
            <Badge
              variant="secondary"
              className="absolute top-2 right-2 bg-primary/80 text-primary-foreground border-0 text-[10px]"
            >
              {genreLabel}
            </Badge>
          )}

          {/* Content overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-3 pt-8">
            {/* Series title */}
            <h4 className="font-semibold text-white text-sm line-clamp-1 drop-shadow-md">
              {item.series_title}
            </h4>

            {/* Episode info */}
            <p className="text-white/70 text-xs mt-1">
              Episode {item.current_episode_number}: {item.current_episode_title}
            </p>
          </div>
        </div>
      </Card>
    </Link>
  );
}
