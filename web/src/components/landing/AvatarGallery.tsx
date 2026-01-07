"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

// Character slugs to showcase in the gallery
const SHOWCASE_CHARACTERS = ["bree", "ethan", "haru", "minji"];

interface CharacterAvatar {
  name: string;
  slug: string;
  avatar_url: string | null;
  archetype: string;
}

// Fallback gradients if images don't load
const FALLBACK_GRADIENTS = [
  "from-purple-400 to-pink-400",
  "from-slate-400 to-purple-500",
  "from-pink-400 to-rose-400",
  "from-amber-400 to-orange-400",
];

export function AvatarGallery() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [characters, setCharacters] = useState<CharacterAvatar[]>([]);
  const [imageErrors, setImageErrors] = useState<Set<number>>(new Set());

  // Fetch characters from API
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "https://api.ep-0.com"}/characters?limit=50`)
      .then((res) => res.json())
      .then((data) => {
        // Filter to showcase characters only
        const showcaseChars = SHOWCASE_CHARACTERS.map((slug) =>
          data.find((c: CharacterAvatar) => c.slug === slug)
        ).filter(Boolean) as CharacterAvatar[];

        if (showcaseChars.length > 0) {
          setCharacters(showcaseChars);
        }
      })
      .catch(() => {
        // Silently fail - will show placeholders
      });
  }, []);

  // Auto-rotate through avatars
  useEffect(() => {
    const count = characters.length || 4;
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % count);
    }, 2500);
    return () => clearInterval(interval);
  }, [characters.length]);

  const handleImageError = (index: number) => {
    setImageErrors((prev) => new Set(prev).add(index));
  };

  // Format archetype for display
  const formatArchetype = (archetype: string) => {
    return archetype
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const displayItems = characters.length > 0 ? characters : null;

  return (
    <div className="relative">
      {/* Character card mock */}
      <div className="w-64 rounded-2xl border bg-muted/50 p-4 shadow-xl">
        {/* Main avatar - rotates */}
        <div
          className={cn(
            "mx-auto mb-4 h-32 w-32 overflow-hidden rounded-xl transition-all duration-500",
            !displayItems || imageErrors.has(activeIndex)
              ? `bg-gradient-to-br ${FALLBACK_GRADIENTS[activeIndex % FALLBACK_GRADIENTS.length]}`
              : "bg-muted"
          )}
        >
          {displayItems && displayItems[activeIndex]?.avatar_url && !imageErrors.has(activeIndex) ? (
            <img
              src={displayItems[activeIndex].avatar_url!}
              alt={displayItems[activeIndex].name}
              className="h-full w-full object-cover"
              onError={() => handleImageError(activeIndex)}
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-4xl text-white/80">
              {displayItems?.[activeIndex]?.name?.[0] || "?"}
            </div>
          )}
        </div>

        {/* Name input mock */}
        <div className="mb-3 rounded-lg border bg-background px-3 py-2 text-center text-sm text-muted-foreground">
          {displayItems?.[activeIndex]?.name || "Your name here"}
        </div>

        {/* Archetype label */}
        <div className="mb-3 text-center">
          <span className="rounded-full bg-purple-600 px-3 py-1 text-xs font-medium text-white">
            {displayItems?.[activeIndex]
              ? formatArchetype(displayItems[activeIndex].archetype)
              : "Your Archetype"}
          </span>
        </div>

        {/* Mini gallery preview */}
        <div className="flex justify-center gap-2">
          {(displayItems || Array(4).fill(null)).map((char, i) => (
            <button
              key={char?.slug || i}
              onClick={() => setActiveIndex(i)}
              className={cn(
                "h-10 w-10 overflow-hidden rounded-lg transition-all",
                i === activeIndex
                  ? "ring-2 ring-purple-500 ring-offset-2 ring-offset-background scale-110"
                  : "opacity-60 hover:opacity-100"
              )}
            >
              {char?.avatar_url && !imageErrors.has(i) ? (
                <img
                  src={char.avatar_url}
                  alt={char.name}
                  className="h-full w-full object-cover"
                  onError={() => handleImageError(i)}
                />
              ) : (
                <div
                  className={cn(
                    "h-full w-full bg-gradient-to-br flex items-center justify-center text-white text-sm font-medium",
                    FALLBACK_GRADIENTS[i % FALLBACK_GRADIENTS.length]
                  )}
                >
                  {char?.name?.[0] || "?"}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Decorative elements */}
      <div className="absolute -right-4 -top-4 h-8 w-8 rounded-full bg-purple-400/20 blur-xl" />
      <div className="absolute -bottom-4 -left-4 h-12 w-12 rounded-full bg-pink-400/20 blur-xl" />
    </div>
  );
}
