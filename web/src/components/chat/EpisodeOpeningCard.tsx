"use client";

import { cn } from "@/lib/utils";

interface EpisodeOpeningCardProps {
  title: string;
  situation: string;
  characterName: string;
  hasBackground?: boolean;
}

/**
 * EpisodeOpeningCard - Simple scene-setting card at conversation start
 *
 * v2.5: Simplified design - matches assistant chat bubble aesthetic
 * - Shows episode title and situation only
 * - No dramatic_question (removed for cleaner UX)
 * - Styled to blend with conversation flow, not stand out
 */
export function EpisodeOpeningCard({
  title,
  situation,
  characterName,
  hasBackground = false,
}: EpisodeOpeningCardProps) {
  return (
    <div className="flex justify-start mb-4">
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-3",
          hasBackground
            ? "bg-black/40 backdrop-blur-sm"
            : "bg-muted"
        )}
      >
        {/* Episode title - subtle label */}
        <p
          className={cn(
            "text-xs font-medium mb-1",
            hasBackground ? "text-white/60" : "text-muted-foreground"
          )}
        >
          {title}
        </p>

        {/* Situation - the main content */}
        <p
          className={cn(
            "text-sm leading-relaxed",
            hasBackground ? "text-white/90" : "text-foreground"
          )}
        >
          {situation}
        </p>
      </div>
    </div>
  );
}
