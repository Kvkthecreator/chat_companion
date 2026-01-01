"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Play, Sparkles } from "lucide-react";
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
 * ADR-004: Each (series, character) pair is a distinct playthrough.
 * Shows character avatar to distinguish between playthroughs.
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

          {/* Character avatar (ADR-004) - top right corner */}
          <div className="absolute top-2 right-2 flex items-center gap-1.5 bg-black/60 backdrop-blur-sm rounded-full pl-1 pr-2.5 py-1">
            <div className={cn(
              "rounded-full overflow-hidden bg-muted flex items-center justify-center shrink-0",
              compact ? "h-5 w-5" : "h-6 w-6"
            )}>
              {item.character_avatar_url ? (
                <img
                  src={item.character_avatar_url}
                  alt={item.character_name}
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className={cn(
                  "font-medium text-white/80",
                  compact ? "text-[8px]" : "text-[10px]"
                )}>
                  {item.character_name.slice(0, 2).toUpperCase()}
                </span>
              )}
            </div>
            <span className={cn(
              "text-white/90 font-medium truncate max-w-[80px]",
              compact ? "text-[10px]" : "text-xs"
            )}>
              {item.character_name}
            </span>
            {item.character_is_user_created && (
              <Sparkles className={cn("text-yellow-400", compact ? "h-2.5 w-2.5" : "h-3 w-3")} />
            )}
          </div>

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
