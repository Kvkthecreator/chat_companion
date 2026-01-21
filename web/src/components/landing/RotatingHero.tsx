"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const HERO_MESSAGES = [
  {
    character: "Your Companion",
    avatar: "/avatars/companion.png",
    message: "Hey! Just checking in. How's your day going so far?",
    story: "Daily Check-in",
  },
  {
    character: "Your Companion",
    avatar: "/avatars/companion.png",
    message: "I remembered you mentioned that big meeting today. How did it go?",
    story: "Remembers You",
  },
  {
    character: "Your Companion",
    avatar: "/avatars/companion.png",
    message: "It's been a few days - wanted to see how you're doing. Everything okay?",
    story: "Always There",
  },
];

export function RotatingHero() {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % HERO_MESSAGES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const current = HERO_MESSAGES[currentIndex];

  return (
    <section className="relative overflow-hidden rounded-3xl border bg-gradient-to-br from-card to-card/50 p-8 md:p-12">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-500/10 via-transparent to-transparent" />

      <div className="relative grid gap-8 md:grid-cols-2 md:gap-12 items-center">
        {/* Left: Copy */}
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full bg-purple-100 dark:bg-purple-900/50 px-4 py-1.5">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
              Always there for you
            </span>
          </div>

          <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            An AI friend that{" "}
            <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              reaches out
            </span>
          </h1>

          <p className="text-lg text-muted-foreground max-w-md">
            Your companion checks in daily, remembers your life, and is always there when you need someone to talk to.
          </p>

          <div className="flex flex-wrap gap-4">
            <Link
              href="/login?next=/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-purple-500/25 transition hover:bg-purple-700 hover:shadow-purple-500/40"
            >
              Get your companion
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
          </div>
        </div>

        {/* Right: Chat preview */}
        <div className="relative">
          <div className="rounded-2xl border bg-background/80 backdrop-blur-sm p-6 shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold">
                {current.character[0]}
              </div>
              <div>
                <p className="font-semibold text-foreground">{current.character}</p>
                <p className="text-xs text-muted-foreground">{current.story}</p>
              </div>
            </div>
            <p className="text-foreground/90 leading-relaxed italic">
              &ldquo;{current.message}&rdquo;
            </p>
            <div className="mt-4 flex items-center gap-2">
              <div className="flex-1 rounded-full bg-muted/50 px-4 py-2 text-sm text-muted-foreground">
                Type your response...
              </div>
            </div>
          </div>

          {/* Dots indicator */}
          <div className="flex justify-center gap-2 mt-4">
            {HERO_MESSAGES.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIndex(idx)}
                className={`h-2 w-2 rounded-full transition-all ${
                  idx === currentIndex ? "bg-purple-500 w-6" : "bg-muted-foreground/30"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
