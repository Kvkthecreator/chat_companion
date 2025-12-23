"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Share2, Check, RefreshCw, Play, Quote, MessageCircle, Lightbulb } from "lucide-react";
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

/**
 * QuizResult v3.0 - Dating Personality Test
 *
 * Viral mechanic: Identity validation ("this is so me")
 * Tone: Therapist who said something uncomfortable
 *
 * Structure:
 * - Pattern (the one-liner)
 * - The Truth (LLM-generated insight)
 * - You Tell Yourself / But Actually (the reveal)
 * - What You Need (advice)
 */
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
        // Ignore errors
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
  const pattern = result.result.pattern || staticContent.pattern;
  const shareText = result.result.share_text || staticContent.shareText;

  // LLM-generated personalized content
  const theTruth = result.result.the_truth || staticContent.theTruth;
  const youTellYourself = result.result.you_tell_yourself || staticContent.youTellYourself;
  const butActually = result.result.but_actually || staticContent.butActually;
  const whatYouNeed = result.result.what_you_need || staticContent.whatYouNeed;

  const handleShare = async () => {
    const shareUrl = `https://ep-0.com/r/${result.share_id}`;
    const fullText = `${shareText}\n\n${shareUrl}`;

    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    if (isMobile && navigator.share) {
      try {
        await navigator.share({
          title: `I'm a ${title}!`,
          text: shareText,
          url: shareUrl,
        });
        return;
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          return;
        }
      }
    }

    try {
      await navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      console.error("Failed to copy to clipboard");
    }
  };

  return (
    <div className="flex flex-col items-center px-4 py-8 pb-16">
      {/* Hero Section */}
      <div className="w-full max-w-lg text-center mb-8">
        {/* Emoji */}
        <div className="text-7xl mb-4">{visuals.emoji}</div>

        {/* Pre-title */}
        <p className="text-muted-foreground text-sm mb-2 uppercase tracking-wider">
          your dating pattern is
        </p>

        {/* Title */}
        <h1 className={cn("text-4xl md:text-5xl font-black mb-3 tracking-tight", visuals.color)}>
          {title}
        </h1>

        {/* Tagline */}
        <p className="text-lg text-muted-foreground italic">
          &ldquo;{tagline}&rdquo;
        </p>
      </div>

      {/* Pattern - The one-liner truth */}
      <Card className="w-full max-w-lg p-6 mb-4 bg-amber-500/5 border-amber-500/20">
        <p className="text-base font-medium text-center leading-relaxed">
          {pattern}
        </p>
      </Card>

      {/* The Truth - The insight that makes them feel seen */}
      {theTruth && (
        <Card className="w-full max-w-lg p-6 mb-4">
          <div className="flex items-center gap-2 mb-4">
            <Quote className="h-5 w-5 text-amber-500 shrink-0" />
            <h2 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">the truth is...</h2>
          </div>
          <p className="text-base leading-relaxed">
            {theTruth}
          </p>
        </Card>
      )}

      {/* You Tell Yourself / But Actually - The reveal */}
      {(youTellYourself || butActually) && (
        <Card className="w-full max-w-lg p-6 mb-4">
          {youTellYourself && (
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <MessageCircle className="h-4 w-4 text-muted-foreground shrink-0" />
                <h2 className="font-semibold text-sm text-muted-foreground">you tell yourself</h2>
              </div>
              <p className="text-base italic text-muted-foreground pl-6">
                &ldquo;{youTellYourself}&rdquo;
              </p>
            </div>
          )}

          {butActually && (
            <div className="pt-4 border-t">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-amber-500 font-bold">but actually...</span>
              </div>
              <p className="text-base leading-relaxed">
                {butActually}
              </p>
            </div>
          )}
        </Card>
      )}

      {/* What You Need - The advice */}
      {whatYouNeed && (
        <Card className="w-full max-w-lg p-6 mb-4 bg-primary/5 border-primary/20">
          <div className="flex items-start gap-3">
            <Lightbulb className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div>
              <h2 className="font-semibold text-sm mb-2">what you actually need</h2>
              <p className="text-sm leading-relaxed">
                {whatYouNeed}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Primary CTA - Share */}
      <div className="w-full max-w-lg mb-3">
        <Button
          onClick={handleShare}
          size="lg"
          className="w-full py-6 text-lg font-semibold rounded-full shadow-lg bg-gradient-to-r from-amber-500 to-rose-500 hover:from-amber-400 hover:to-rose-400"
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
      <div className="w-full max-w-lg mb-8">
        <Button
          onClick={onPlayAgain}
          variant="outline"
          className="w-full py-3 rounded-full"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          try again
        </Button>
      </div>

      {/* Try the other quiz */}
      <div className="w-full max-w-lg mb-8 text-center">
        <Link
          href="/play/freak"
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          Try the Unhinged Test instead
        </Link>
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
                <Card className="overflow-hidden border-2 border-transparent hover:border-amber-500/30 transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
                  <div className="relative aspect-[16/10] overflow-hidden bg-muted">
                    {series.cover_image_url && (
                      <img
                        src={series.cover_image_url}
                        alt={series.title}
                        className="absolute inset-0 w-full h-full object-cover"
                      />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                    <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="w-12 h-12 rounded-full bg-white/90 flex items-center justify-center shadow-lg">
                        <Play className="h-5 w-5 text-amber-500 fill-amber-500 ml-0.5" />
                      </div>
                    </div>
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
