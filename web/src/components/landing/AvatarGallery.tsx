"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

// Example character avatars from Supabase storage
// These showcase the variety users can create
const EXAMPLE_AVATARS = [
  {
    name: "Bold",
    // Each has gradient fallback if image doesn't load
    gradient: "from-purple-400 to-pink-400",
  },
  {
    name: "Mysterious",
    gradient: "from-slate-400 to-purple-500",
  },
  {
    name: "Caring",
    gradient: "from-pink-400 to-rose-400",
  },
  {
    name: "Playful",
    gradient: "from-amber-400 to-orange-400",
  },
];

export function AvatarGallery() {
  const [activeIndex, setActiveIndex] = useState(0);

  // Auto-rotate through avatars
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % EXAMPLE_AVATARS.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative">
      {/* Character card mock */}
      <div className="w-64 rounded-2xl border bg-muted/50 p-4 shadow-xl">
        {/* Main avatar - rotates */}
        <div
          className={cn(
            "mx-auto mb-4 h-32 w-32 overflow-hidden rounded-xl bg-gradient-to-br transition-all duration-500",
            EXAMPLE_AVATARS[activeIndex].gradient
          )}
        >
          <div className="flex h-full w-full items-center justify-center text-4xl text-white/80">
            {EXAMPLE_AVATARS[activeIndex].name[0]}
          </div>
        </div>

        {/* Name input mock */}
        <div className="mb-3 rounded-lg border bg-background px-3 py-2 text-center text-sm text-muted-foreground">
          Your name here
        </div>

        {/* Archetype chips - highlight active */}
        <div className="flex flex-wrap justify-center gap-1.5">
          {EXAMPLE_AVATARS.map((avatar, i) => (
            <button
              key={avatar.name}
              onClick={() => setActiveIndex(i)}
              className={cn(
                "rounded-full px-2 py-0.5 text-xs transition-all",
                i === activeIndex
                  ? "bg-purple-600 text-white scale-105"
                  : "bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-800/50"
              )}
            >
              {avatar.name}
            </button>
          ))}
        </div>

        {/* Mini gallery preview */}
        <div className="mt-4 flex justify-center gap-2">
          {EXAMPLE_AVATARS.map((avatar, i) => (
            <button
              key={`thumb-${avatar.name}`}
              onClick={() => setActiveIndex(i)}
              className={cn(
                "h-8 w-8 rounded-lg bg-gradient-to-br transition-all",
                avatar.gradient,
                i === activeIndex
                  ? "ring-2 ring-purple-500 ring-offset-2 ring-offset-background scale-110"
                  : "opacity-60 hover:opacity-100"
              )}
            >
              <span className="sr-only">{avatar.name}</span>
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
