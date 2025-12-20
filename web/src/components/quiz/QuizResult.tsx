"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Share2, Check, RefreshCw, Sparkles, AlertCircle, Heart } from "lucide-react";
import { TROPE_CONTENT } from "@/lib/quiz-data";
import type { RomanticTrope } from "@/types";
import { TROPE_VISUALS } from "@/types";

interface QuizResultProps {
  trope: RomanticTrope;
  onPlayAgain: () => void;
}

// Episode 0 series data
const EPISODE_0_SERIES = [
  {
    id: "hometown-crush",
    title: "Hometown Crush",
    slug: "hometown-crush",
    tagline: "Running into your ex at a friend's wedding",
    coverUrl: null,
  },
  {
    id: "coffee-shop-crush",
    title: "Coffee Shop Crush",
    slug: "coffee-shop-crush",
    tagline: "The barista who remembers your order",
    coverUrl: null,
  },
];

export function QuizResult({ trope, onPlayAgain }: QuizResultProps) {
  const [copied, setCopied] = useState(false);
  const content = TROPE_CONTENT[trope];
  const visuals = TROPE_VISUALS[trope];

  const handleShare = async () => {
    const shareUrl = `${window.location.origin}/play`;
    const shareText = content.shareText;

    if (navigator.share) {
      try {
        await navigator.share({
          title: `I'm a ${content.title}!`,
          text: shareText,
          url: shareUrl,
        });
        return;
      } catch {
        // User cancelled or share failed, fall through to copy
      }
    }

    // Fallback to clipboard
    try {
      await navigator.clipboard.writeText(`${shareText}\n${shareUrl}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  // Get compatible trope names
  const compatibleNames = content.compatibleWith.map(t => TROPE_CONTENT[t].title);

  return (
    <div className="flex flex-col items-center min-h-screen px-4 py-8">
      {/* Hero Section */}
      <div className="w-full max-w-lg text-center mb-8">
        {/* Emoji */}
        <div className="text-7xl mb-4">{visuals.emoji}</div>

        {/* Pre-title */}
        <p className="text-muted-foreground text-sm mb-2 uppercase tracking-wider">
          your red flag is...
        </p>

        {/* Title */}
        <h1 className={cn("text-4xl md:text-5xl font-black mb-3 tracking-tight", visuals.color)}>
          {content.title}
        </h1>

        {/* Tagline */}
        <p className="text-lg text-muted-foreground italic">
          {content.tagline}
        </p>
      </div>

      {/* Main Description */}
      <Card className="w-full max-w-lg p-6 mb-6">
        <p className="text-base leading-relaxed">
          {content.description}
        </p>
      </Card>

      {/* In Relationships Section */}
      <Card className="w-full max-w-lg p-6 mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Heart className="h-5 w-5 text-pink-500" />
          <h2 className="font-semibold">In Relationships</h2>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {content.inRelationships}
        </p>
      </Card>

      {/* Strengths & Challenges */}
      <div className="w-full max-w-lg grid md:grid-cols-2 gap-4 mb-6">
        {/* Strengths */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-green-500" />
            <h3 className="font-semibold text-sm">Strengths</h3>
          </div>
          <ul className="space-y-2">
            {content.strengths.map((strength, i) => (
              <li key={i} className="text-xs text-muted-foreground leading-relaxed">
                {strength}
              </li>
            ))}
          </ul>
        </Card>

        {/* Challenges */}
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="h-4 w-4 text-amber-500" />
            <h3 className="font-semibold text-sm">Challenges</h3>
          </div>
          <ul className="space-y-2">
            {content.challenges.map((challenge, i) => (
              <li key={i} className="text-xs text-muted-foreground leading-relaxed">
                {challenge}
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {/* Advice */}
      <Card className="w-full max-w-lg p-6 mb-6 bg-primary/5 border-primary/20">
        <p className="text-sm text-center italic">
          "{content.advice}"
        </p>
      </Card>

      {/* Compatibility */}
      <div className="w-full max-w-lg mb-8 text-center">
        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
          you vibe with
        </p>
        <p className="text-sm font-medium">
          {compatibleNames.join(" & ")}
        </p>
      </div>

      {/* Primary CTA - Share */}
      <div className="w-full max-w-lg mb-4">
        <Button
          onClick={handleShare}
          size="lg"
          className="w-full py-6 text-lg font-semibold rounded-full"
        >
          {copied ? (
            <>
              <Check className="h-5 w-5 mr-2" />
              copied!
            </>
          ) : (
            <>
              <Share2 className="h-5 w-5 mr-2" />
              share result
            </>
          )}
        </Button>
      </div>

      {/* Secondary: Play Again */}
      <div className="w-full max-w-lg mb-12">
        <Button
          onClick={onPlayAgain}
          variant="outline"
          className="w-full py-3 rounded-full"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          try again
        </Button>
      </div>

      {/* Episode 0 CTA Section */}
      <div className="w-full max-w-lg">
        <div className="text-center mb-6">
          <h3 className="text-lg font-semibold mb-1">ready for the real thing?</h3>
          <p className="text-sm text-muted-foreground">
            try episode 0 — free interactive romance stories
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {EPISODE_0_SERIES.map((series) => (
            <Link
              key={series.id}
              href={`/series/${series.slug}`}
              className="group"
            >
              <Card className="overflow-hidden hover:ring-2 hover:ring-primary/50 transition-all">
                <div className="aspect-[4/3] bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
                  <span className="text-3xl font-bold text-primary/30">
                    {series.title[0]}
                  </span>
                </div>
                <div className="p-3">
                  <h4 className="font-semibold text-sm group-hover:text-primary transition-colors line-clamp-1">
                    {series.title}
                  </h4>
                  {series.tagline && (
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {series.tagline}
                    </p>
                  )}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-8 text-muted-foreground/60 text-xs">
        <a href="/" className="hover:text-foreground transition-colors">
          ep-0.com/play
        </a>
      </div>
    </div>
  );
}
