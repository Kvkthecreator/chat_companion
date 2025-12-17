"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Play, BookOpen } from "lucide-react";
import type { SeriesSummary, World } from "@/types";

interface SeriesDiscoveryCardProps {
  series: SeriesSummary;
  world?: World;
  className?: string;
  featured?: boolean;
}

/**
 * Series card for discovery/browse UI.
 * Shows series info with episode count and entry point.
 */
export function SeriesDiscoveryCard({ series, world, className, featured }: SeriesDiscoveryCardProps) {
  return (
    <Link href={`/series/${series.slug}`}>
      <Card
        className={cn(
          "relative overflow-hidden cursor-pointer transition-all duration-200",
          "hover:shadow-xl hover:-translate-y-1 hover:ring-2 hover:ring-primary/50",
          "group h-full",
          featured && "ring-2 ring-primary/30",
          className
        )}
      >
        {/* Cover image or gradient */}
        <div className={cn("relative overflow-hidden", featured ? "aspect-[16/9]" : "aspect-[16/10]")}>
          {series.cover_image_url ? (
            <img
              src={series.cover_image_url}
              alt={series.title}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-blue-600/40 via-purple-500/30 to-pink-500/20" />
          )}

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />

          {/* Play indicator on hover */}
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="h-14 w-14 rounded-full bg-white/95 flex items-center justify-center shadow-xl">
              <Play className="h-6 w-6 text-primary ml-0.5" fill="currentColor" />
            </div>
          </div>

          {/* World badge */}
          {world && (
            <Badge
              variant="secondary"
              className="absolute top-2 left-2 bg-black/60 text-white border-0 text-[10px]"
            >
              {world.name}
            </Badge>
          )}

          {/* Series type badge */}
          <Badge
            variant="secondary"
            className="absolute top-2 right-2 bg-primary/80 text-primary-foreground border-0 text-[10px] capitalize"
          >
            {series.series_type}
          </Badge>

          {/* Content overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-4 space-y-2">
            {/* Title */}
            <h4 className={cn(
              "font-semibold text-white drop-shadow-md line-clamp-2",
              featured ? "text-lg" : "text-sm"
            )}>
              {series.title}
            </h4>

            {/* Tagline */}
            {series.tagline && (
              <p className="text-white/80 text-xs italic line-clamp-2 drop-shadow-md">
                {series.tagline}
              </p>
            )}

            {/* Episode count */}
            <div className="flex items-center gap-2 text-white/70 text-xs">
              <BookOpen className="h-3 w-3" />
              <span>{series.total_episodes} episode{series.total_episodes !== 1 ? 's' : ''}</span>
              {series.genre && (
                <>
                  <span>·</span>
                  <span className="capitalize">{series.genre.replace('_', ' ')}</span>
                </>
              )}
            </div>
          </div>
        </div>
      </Card>
    </Link>
  );
}
