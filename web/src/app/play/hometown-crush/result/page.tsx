"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Share2, RefreshCw, BookOpen, Check } from "lucide-react";
import Link from "next/link";
import type { RomanticTrope, RomanticTropeResult } from "@/types";

// Trope visual metadata for display
const TROPE_META: Record<RomanticTrope, { emoji: string; color: string }> = {
  slow_burn: { emoji: "🕯️", color: "text-amber-500" },
  second_chance: { emoji: "🌅", color: "text-rose-500" },
  all_in: { emoji: "💫", color: "text-yellow-500" },
  push_pull: { emoji: "⚡", color: "text-purple-500" },
  slow_reveal: { emoji: "🌙", color: "text-violet-500" },
};

interface ResultData {
  evaluation: RomanticTropeResult;
  shareUrl: string;
  characterName: string;
}

function HometownCrushResultContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session");

  const [result, setResult] = useState<ResultData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      router.replace("/play/hometown-crush");
      return;
    }

    const fetchResult = async () => {
      try {
        const storedState = sessionStorage.getItem(`hometown-crush-${sessionId}`);
        const anonymousId = storedState ? JSON.parse(storedState).anonymousId : undefined;

        const response = await api.games.getResult("hometown-crush", sessionId, anonymousId);
        setResult({
          evaluation: response.result as RomanticTropeResult,
          shareUrl: response.share_url,
          characterName: response.character_name,
        });
      } catch (err) {
        console.error("Failed to fetch result:", err);
        setError("Failed to load your result. Please try again.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchResult();
  }, [sessionId, router]);

  const handleShare = async () => {
    if (!result) return;

    const shareUrl = `${window.location.origin}${result.shareUrl}`;
    const shareText = `I'm ${result.evaluation.title} ${TROPE_META[result.evaluation.trope]?.emoji || "💕"} - "${result.evaluation.tagline}"\n\nWhat's your romantic trope?`;

    if (navigator.share) {
      try {
        await navigator.share({
          title: `I'm ${result.evaluation.title}!`,
          text: shareText,
          url: shareUrl,
        });
        return;
      } catch {
        // User cancelled or share failed, fall through to copy
      }
    }

    try {
      await navigator.clipboard.writeText(`${shareText}\n${shareUrl}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handlePlayAgain = () => {
    router.push("/play/hometown-crush");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 border-4 border-muted border-t-primary rounded-full animate-spin" />
          <p className="text-muted-foreground">Reading you for filth...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-destructive mb-4">{error || "Something went wrong"}</p>
          <Button onClick={handlePlayAgain} variant="outline">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  const trope = result.evaluation.trope;
  const meta = TROPE_META[trope] || TROPE_META.slow_burn;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Background gradient */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 via-purple-500/5 to-pink-500/10" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center min-h-screen px-4 py-8">
        {/* Result Card */}
        <Card className="w-full max-w-md p-6 shadow-xl">
          {/* Header */}
          <p className="text-center text-muted-foreground text-xs uppercase tracking-wider mb-3">
            Your Romantic Trope
          </p>

          {/* Emoji + Title */}
          <div className="text-5xl text-center mb-2">{meta.emoji}</div>
          <h1 className={cn("text-2xl font-bold text-center mb-1", meta.color)}>
            {result.evaluation.title}
          </h1>

          {/* Tagline */}
          <p className="text-center text-muted-foreground italic text-sm mb-5">
            &ldquo;{result.evaluation.tagline}&rdquo;
          </p>

          {/* The Read - Brutal Truth */}
          <div className="mb-5 p-4 bg-muted/50 rounded-xl">
            <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider font-medium">
              The Read
            </p>
            <p className="text-sm leading-relaxed">
              {result.evaluation.the_read || result.evaluation.description}
            </p>
          </div>

          {/* Your Receipts - Evidence */}
          {result.evaluation.evidence && result.evaluation.evidence.length > 0 && (
            <div className="mb-5">
              <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider font-medium">
                Your Receipts
              </p>
              <ul className="space-y-2">
                {result.evaluation.evidence.map((observation, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className={cn("mt-0.5", meta.color)}>→</span>
                    <span>{observation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* The Moment - Callback Quote */}
          {result.evaluation.callback_quote && (
            <div className="mb-5 p-3 bg-primary/5 rounded-xl border border-primary/10">
              <p className="text-xs text-muted-foreground mb-1 uppercase tracking-wider">
                The Moment We Knew
              </p>
              <p className="text-sm italic">
                {result.evaluation.callback_quote}
              </p>
            </div>
          )}

          {/* Coaching - Do's and Don'ts */}
          {result.evaluation.coaching && (
            <div className="mb-5">
              <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider font-medium">
                Friendly Advice
              </p>
              <div className="grid grid-cols-2 gap-3">
                {/* Do's */}
                <div className="space-y-1.5">
                  {result.evaluation.coaching.do?.slice(0, 2).map((item, i) => (
                    <div key={i} className="text-xs flex items-start gap-1.5">
                      <span className="text-green-500 flex-shrink-0">✓</span>
                      <span className="text-muted-foreground">{item}</span>
                    </div>
                  ))}
                </div>
                {/* Don'ts */}
                <div className="space-y-1.5">
                  {result.evaluation.coaching.dont?.slice(0, 2).map((item, i) => (
                    <div key={i} className="text-xs flex items-start gap-1.5">
                      <span className="text-red-500 flex-shrink-0">✗</span>
                      <span className="text-muted-foreground">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Cultural Roast + Refs */}
          {result.evaluation.cultural_refs && result.evaluation.cultural_refs.length > 0 && (
            <div className="mb-4">
              <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wider font-medium">
                You In The Wild
              </p>
              {result.evaluation.cultural_roast && (
                <p className="text-xs text-muted-foreground italic mb-2">
                  {result.evaluation.cultural_roast}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                {result.evaluation.cultural_refs.slice(0, 3).map((ref, i) => (
                  <span key={i} className="text-xs bg-muted px-2 py-1 rounded-full">
                    {ref.title}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Match strength */}
          <div className="pt-3 border-t">
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>Match</span>
              <span>{Math.round(result.evaluation.confidence * 100)}%</span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${result.evaluation.confidence * 100}%` }}
              />
            </div>
          </div>
        </Card>

        {/* Primary CTA - Share */}
        <div className="mt-6 w-full max-w-md">
          <Button
            onClick={handleShare}
            size="lg"
            className="w-full py-6 text-lg font-semibold rounded-full"
          >
            {copied ? (
              <>
                <Check className="h-5 w-5 mr-2" />
                Copied!
              </>
            ) : (
              <>
                <Share2 className="h-5 w-5 mr-2" />
                Send to the Group Chat
              </>
            )}
          </Button>
        </div>

        {/* Secondary: Play Again + Explore */}
        <div className="mt-4 flex gap-3 w-full max-w-md">
          <Button
            onClick={handlePlayAgain}
            variant="outline"
            className="flex-1 py-3 rounded-full"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Try Again
          </Button>
          <Button
            asChild
            variant="outline"
            className="flex-1 py-3 rounded-full"
          >
            <Link href="/series">
              <BookOpen className="h-4 w-4 mr-2" />
              More Stories
            </Link>
          </Button>
        </div>

        {/* Footer */}
        <div className="mt-8 text-muted-foreground/60 text-xs">
          <a href="/" className="hover:text-foreground transition-colors">
            ep-0.com
          </a>
        </div>
      </div>
    </div>
  );
}

export default function HometownCrushResultPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 mx-auto mb-4 border-4 border-muted border-t-primary rounded-full animate-spin" />
          <p className="text-muted-foreground">Reading you for filth...</p>
        </div>
      </div>
    }>
      <HometownCrushResultContent />
    </Suspense>
  );
}
