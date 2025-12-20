"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { RomanticTrope, RomanticTropeResult } from "@/types";

// Trope visual metadata for display
const TROPE_META: Record<RomanticTrope, { emoji: string; color: string; gradient: string }> = {
  slow_burn: {
    emoji: "🕯️",
    color: "text-amber-400",
    gradient: "from-amber-500/20 to-orange-500/20",
  },
  second_chance: {
    emoji: "🌅",
    color: "text-rose-400",
    gradient: "from-rose-500/20 to-pink-500/20",
  },
  all_in: {
    emoji: "💫",
    color: "text-yellow-400",
    gradient: "from-yellow-500/20 to-amber-500/20",
  },
  push_pull: {
    emoji: "⚡",
    color: "text-purple-400",
    gradient: "from-purple-500/20 to-indigo-500/20",
  },
  slow_reveal: {
    emoji: "🌙",
    color: "text-violet-400",
    gradient: "from-violet-500/20 to-purple-500/20",
  },
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
        // Get anonymousId from session storage for anonymous users
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

    // Try native share API first
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

    // Fallback to clipboard
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
      <div className="min-h-screen bg-gradient-to-b from-amber-950 via-rose-950 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 border-4 border-white/20 border-t-white/80 rounded-full animate-spin" />
          <p className="text-white/60">Reading you for filth...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-amber-950 via-rose-950 to-slate-950 flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || "Something went wrong"}</p>
          <Button onClick={handlePlayAgain} variant="outline" className="text-white border-white/20">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  const trope = result.evaluation.trope;
  const meta = TROPE_META[trope] || TROPE_META.slow_burn;

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-950 via-rose-950 to-slate-950 text-white">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-amber-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-rose-500/20 rounded-full blur-3xl" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center min-h-screen px-4 py-8">
        {/* Result Card - Main shareable content */}
        <div className={cn(
          "w-full max-w-md p-6 rounded-3xl backdrop-blur-xl border border-white/10",
          "bg-gradient-to-br",
          meta.gradient
        )}>
          {/* Header */}
          <p className="text-center text-white/50 text-xs uppercase tracking-wider mb-2">
            Your Romantic Trope
          </p>

          {/* Emoji + Title */}
          <div className="text-5xl text-center mb-2">{meta.emoji}</div>
          <h1 className={cn("text-2xl font-bold text-center mb-1", meta.color)}>
            {result.evaluation.title}
          </h1>

          {/* Tagline */}
          <p className="text-center text-white/70 italic text-sm mb-4">
            &ldquo;{result.evaluation.tagline}&rdquo;
          </p>

          {/* The Read - Brutal Truth */}
          <div className="mb-5 p-4 bg-black/20 rounded-xl border border-white/5">
            <p className="text-xs text-white/50 mb-2 uppercase tracking-wider font-medium">
              The Read
            </p>
            <p className="text-sm text-white/90 leading-relaxed">
              {result.evaluation.the_read || result.evaluation.description}
            </p>
          </div>

          {/* Your Receipts - Evidence */}
          {result.evaluation.evidence && result.evaluation.evidence.length > 0 && (
            <div className="mb-5">
              <p className="text-xs text-white/50 mb-2 uppercase tracking-wider font-medium">
                Your Receipts
              </p>
              <ul className="space-y-2">
                {result.evaluation.evidence.map((observation, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-white/80">
                    <span className={cn("mt-0.5", meta.color)}>→</span>
                    <span>{observation}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* The Moment - Callback Quote */}
          {result.evaluation.callback_quote && (
            <div className="mb-5 p-3 bg-white/5 rounded-xl border border-white/10">
              <p className="text-xs text-white/50 mb-1 uppercase tracking-wider">
                The Moment We Knew
              </p>
              <p className="text-sm text-white/90 italic">
                {result.evaluation.callback_quote}
              </p>
            </div>
          )}

          {/* Coaching - Do's and Don'ts */}
          {result.evaluation.coaching && (
            <div className="mb-5">
              <p className="text-xs text-white/50 mb-2 uppercase tracking-wider font-medium">
                Friendly Advice
              </p>
              <div className="grid grid-cols-2 gap-3">
                {/* Do's */}
                <div className="space-y-1">
                  {result.evaluation.coaching.do?.slice(0, 2).map((item, i) => (
                    <div key={i} className="text-xs text-white/70 flex items-start gap-1">
                      <span className="text-green-400 flex-shrink-0">✓</span>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
                {/* Don'ts */}
                <div className="space-y-1">
                  {result.evaluation.coaching.dont?.slice(0, 2).map((item, i) => (
                    <div key={i} className="text-xs text-white/70 flex items-start gap-1">
                      <span className="text-red-400 flex-shrink-0">✗</span>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Cultural Roast + Refs */}
          {result.evaluation.cultural_refs && result.evaluation.cultural_refs.length > 0 && (
            <div className="mb-4">
              <p className="text-xs text-white/50 mb-2 uppercase tracking-wider font-medium">
                You In The Wild
              </p>
              {result.evaluation.cultural_roast && (
                <p className="text-xs text-white/60 italic mb-2">
                  {result.evaluation.cultural_roast}
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                {result.evaluation.cultural_refs.slice(0, 3).map((ref, i) => (
                  <span key={i} className="text-xs bg-white/10 px-2 py-1 rounded-full text-white/70">
                    {ref.title}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Match strength - smaller */}
          <div className="pt-3 border-t border-white/10">
            <div className="flex justify-between text-xs text-white/40 mb-1">
              <span>Match</span>
              <span>{Math.round(result.evaluation.confidence * 100)}%</span>
            </div>
            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full bg-gradient-to-r", "from-amber-400 to-rose-400")}
                style={{ width: `${result.evaluation.confidence * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Primary CTA - Share */}
        <div className="mt-6 w-full max-w-md">
          <Button
            onClick={handleShare}
            size="lg"
            className={cn(
              "w-full py-6 text-lg font-semibold rounded-full",
              "bg-gradient-to-r from-amber-500 to-rose-500 hover:from-amber-400 hover:to-rose-400",
              "shadow-xl shadow-rose-500/20"
            )}
          >
            {copied ? "Copied! 📋" : "Send to the Group Chat 💬"}
          </Button>
        </div>

        {/* Secondary: Play Again + Explore */}
        <div className="mt-4 flex gap-3 w-full max-w-md">
          <Button
            onClick={handlePlayAgain}
            variant="outline"
            className="flex-1 py-3 rounded-full border-white/20 text-white hover:bg-white/10 text-sm"
          >
            Try Different Character
          </Button>
          <a
            href="/series"
            className={cn(
              "flex-1 py-3 rounded-full border border-white/20 text-white hover:bg-white/10 text-sm",
              "flex items-center justify-center transition-colors"
            )}
          >
            More Stories →
          </a>
        </div>

        {/* Footer */}
        <div className="mt-6 text-white/30 text-xs">
          <a href="/" className="hover:text-white/50 transition-colors">
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
      <div className="min-h-screen bg-gradient-to-b from-amber-950 via-rose-950 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 border-4 border-white/20 border-t-white/80 rounded-full animate-spin" />
          <p className="text-white/60">Reading you for filth...</p>
        </div>
      </div>
    }>
      <HometownCrushResultContent />
    </Suspense>
  );
}
