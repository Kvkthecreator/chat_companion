"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Play } from "lucide-react";
import type { ContinueWatchingItem } from "@/types";

interface ContinueWatchingCardProps {
  item: ContinueWatchingItem;
  className?: string;
  compact?: boolean;
}

/**
 * Card for "Continue Watching" section.
 * Links directly to chat with the current episode.
 *
 * compact: Smaller card for grid layout (no genre badge, smaller text)
 */
export function ContinueWatchingCard({ item, className, compact }: ContinueWatchingCardProps) {
  return (
    <Link href={`/chat/${item.character_id}?episode=${item.current_episode_id}`}>
      <Card
        className={cn(
          "relative overflow-hidden cursor-pointer transition-all duration-200",
          "hover:shadow-xl hover:-translate-y-1 hover:ring-2 hover:ring-primary/50",
          "group",
          !compact && "flex-shrink-0 snap-start w-[280px] sm:w-[320px]",
          className
        )}
      >
        {/* Cover image */}
        <div className={cn("relative overflow-hidden", compact ? "aspect-[16/7]" : "aspect-[16/9]")}>
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
            <div className={cn(
              "rounded-full bg-white/95 flex items-center justify-center shadow-xl",
              compact ? "h-10 w-10" : "h-14 w-14"
            )}>
              <Play className={cn("text-primary ml-0.5", compact ? "h-4 w-4" : "h-6 w-6")} fill="currentColor" />
            </div>
          </div>

          {/* Progress bar */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/20">
            <div
              className="h-full bg-primary"
              style={{ width: `${Math.min((item.current_episode_number / item.total_episodes) * 100, 100)}%` }}
            />
          </div>

          {/* Content overlay */}
          <div className={cn("absolute bottom-0 left-0 right-0", compact ? "p-2 pt-6" : "p-3 pt-8")}>
            {/* Series title */}
            <h4 className={cn(
              "font-semibold text-white line-clamp-1 drop-shadow-md",
              compact ? "text-xs" : "text-sm"
            )}>
              {item.series_title}
            </h4>

            {/* Episode info */}
            <p className={cn("text-white/70 mt-0.5", compact ? "text-[10px]" : "text-xs mt-1")}>
              Ep {item.current_episode_number}: {item.current_episode_title}
            </p>
          </div>
        </div>
      </Card>
    </Link>
  );
}
