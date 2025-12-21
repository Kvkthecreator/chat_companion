"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Share2, Check, RefreshCw, Sparkles, Heart, Play, Quote } from "lucide-react";
import { TROPE_CONTENT } from "@/lib/quiz-data";
import type { RomanticTrope, QuizEvaluateResponse } from "@/types";
import { TROPE_VISUALS } from "@/types";

interface QuizResultProps {
  result: QuizEvaluateResponse;
  onPlayAgain: () => void;
}

interface Series {
  id: string;
  title: string;
  slug: string;
  tagline?: string;
  cover_image_url?: string;
}

export function QuizResult({ result, onPlayAgain }: QuizResultProps) {
  const [copied, setCopied] = useState(false);
  const [featuredSeries, setFeaturedSeries] = useState<Series[]>([]);

  // Fetch featured series on mount
  useEffect(() => {
    async function fetchSeries() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "https://api.ep-0.com"}/series?featured=true&limit=2`
        );
        if (res.ok) {
          const data = await res.json();
          setFeaturedSeries(data);
        }
      } catch {
        // Ignore errors - cards will just not show images
      }
    }
    fetchSeries();
  }, []);

  const trope = result.result.trope as RomanticTrope;
  const visuals = TROPE_VISUALS[trope];
  const staticContent = TROPE_CONTENT[trope];

  // Use API result for personalized content, fallback to static
  const title = result.result.title || staticContent.title;
  const tagline = result.result.tagline || staticContent.tagline;
  const description = result.result.description || staticContent.description;
  const shareText = result.result.share_text || staticContent.shareText;
  const evidence = result.result.evidence || [];
  const vibeCheck = result.result.vibe_check;
  const yourPeople = result.result.your_people || staticContent.yourPeople;

  const handleShare = async () => {
    // Use clean URL format (no www., consistent branding)
    const shareUrl = `https://ep-0.com/r/${result.share_id}`;
    const fullText = `${shareText}\n\n${shareUrl}`;

    // Check if we're on mobile (navigator.share works best there)
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    // Only use native share on mobile where it works well
    if (isMobile && navigator.share) {
      try {
        await navigator.share({
          title: `I'm a ${title}!`,
          text: shareText,
          url: shareUrl,
        });
        return;
      } catch (err) {
        // User cancelled or share failed - check if it's an abort
        if (err instanceof Error && err.name === "AbortError") {
          return; // User cancelled, don't fall through
        }
        // Other error, fall through to clipboard
      }
    }

    // Desktop: use clipboard copy directly
    try {
      await navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Last resort: use a textarea for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = fullText;
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      textarea.style.top = "0";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      try {
        document.execCommand("copy");
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch {
        console.error("Failed to copy to clipboard");
      }
      document.body.removeChild(textarea);
    }
  };

  // Get compatible trope names
  const compatibleNames = staticContent.compatibleWith.map(t => TROPE_CONTENT[t].title);

  return (
    <div className="flex flex-col items-center px-4 py-8 pb-16">
      {/* Hero Section */}
      <div className="w-full max-w-lg text-center mb-8">
        {/* Emoji */}
        <div className="text-7xl mb-4">{visuals.emoji}</div>

        {/* Pre-title */}
        <p className="text-muted-foreground text-sm mb-2 uppercase tracking-wider">
          your romance type is
        </p>

        {/* Title */}
        <h1 className={cn("text-4xl md:text-5xl font-black mb-3 tracking-tight", visuals.color)}>
          {title}
        </h1>

        {/* Tagline */}
        <p className="text-lg text-muted-foreground italic">
          {tagline}
        </p>
      </div>

      {/* Vibe Check - The devastating one-liner */}
      {vibeCheck && (
        <Card className="w-full max-w-lg p-6 mb-4 bg-primary/5 border-primary/20">
          <div className="flex items-start gap-3">
            <Quote className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <p className="text-base font-medium italic leading-relaxed">
              {vibeCheck}
            </p>
          </div>
        </Card>
      )}

      {/* Main Description */}
      <Card className="w-full max-w-lg p-6 mb-4">
        <p className="text-base leading-relaxed">
          {description}
        </p>
      </Card>

      {/* LLM-Generated Evidence - The callouts */}
      {evidence.length > 0 && (
        <Card className="w-full max-w-lg p-6 mb-4">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="h-5 w-5 text-pink-500" />
            <h2 className="font-semibold">we noticed...</h2>
          </div>
          <ul className="space-y-3">
            {evidence.map((item, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-muted-foreground leading-relaxed">
                <span className="text-primary font-bold shrink-0">{i + 1}.</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {/* Strengths & Challenges - MBTI style */}
      <Card className="w-full max-w-lg p-6 mb-4">
        <div className="grid grid-cols-2 gap-6">
          {/* Strengths */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-green-500">✓</span>
              <h2 className="font-semibold text-sm">strengths</h2>
            </div>
            <ul className="space-y-2">
              {staticContent.strengths.map((strength, i) => (
                <li key={i} className="text-xs text-muted-foreground leading-relaxed">
                  {strength}
                </li>
              ))}
            </ul>
          </div>
          {/* Challenges */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-amber-500">!</span>
              <h2 className="font-semibold text-sm">watch out for</h2>
            </div>
            <ul className="space-y-2">
              {staticContent.challenges.map((challenge, i) => (
                <li key={i} className="text-xs text-muted-foreground leading-relaxed">
                  {challenge}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Card>

      {/* In Relationships */}
      <Card className="w-full max-w-lg p-6 mb-4">
        <h2 className="font-semibold text-sm mb-3">in relationships</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {staticContent.inRelationships}
        </p>
      </Card>

      {/* Advice */}
      <Card className="w-full max-w-lg p-6 mb-4 bg-primary/5 border-primary/20">
        <h2 className="font-semibold text-sm mb-2">advice for you</h2>
        <p className="text-sm text-muted-foreground italic leading-relaxed">
          {staticContent.advice}
        </p>
      </Card>

      {/* Your People - Cultural references */}
      {yourPeople && yourPeople.length > 0 && (
        <Card className="w-full max-w-lg p-6 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Heart className="h-5 w-5 text-pink-500" />
            <h2 className="font-semibold">your people</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            {yourPeople.join(" • ")}
          </p>
        </Card>
      )}

      {/* Compatibility */}
      <div className="w-full max-w-lg mb-8 text-center">
        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">
          Most compatible with
        </p>
        <p className="text-sm font-medium">
          {compatibleNames.join(" & ")}
        </p>
      </div>

      {/* Primary CTA - Share */}
      <div className="w-full max-w-lg mb-3">
        <Button
          onClick={handleShare}
          size="lg"
          className="w-full py-6 text-lg font-semibold rounded-full shadow-lg"
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
      {featuredSeries.length > 0 && (
        <div className="w-full max-w-lg">
          <div className="text-center mb-6">
            <h3 className="text-xl font-semibold mb-2">ready for the real thing?</h3>
            <p className="text-sm text-muted-foreground">
              try episode 0 — free interactive romance stories
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {featuredSeries.map((series) => (
              <Link
                key={series.id}
                href={`/series/${series.slug}`}
                className="group"
              >
                <Card className="overflow-hidden border-2 border-transparent hover:border-primary/30 transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
                  {/* Cover with actual image */}
                  <div className="relative aspect-[16/10] overflow-hidden bg-muted">
                    {series.cover_image_url && (
                      <img
                        src={series.cover_image_url}
                        alt={series.title}
                        className="absolute inset-0 w-full h-full object-cover"
                      />
                    )}
                    {/* Gradient overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                    {/* Play icon on hover */}
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="w-12 h-12 rounded-full bg-white/90 flex items-center justify-center shadow-lg">
                        <Play className="h-5 w-5 text-primary fill-primary ml-0.5" />
                      </div>
                    </div>
                    {/* Title overlay */}
                    <div className="absolute bottom-0 left-0 right-0 p-3">
                      <h4 className="font-semibold text-sm text-white drop-shadow-md line-clamp-1">
                        {series.title}
                      </h4>
                      {series.tagline && (
                        <p className="text-xs text-white/80 line-clamp-1 mt-0.5 drop-shadow-md">
                          {series.tagline}
                        </p>
                      )}
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-10 text-muted-foreground/60 text-xs">
        <Link href="/" className="hover:text-foreground transition-colors">
          ep-0.com
        </Link>
      </div>
    </div>
  );
}
