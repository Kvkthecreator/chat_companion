"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function PlayPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-purple-950 to-rose-950 text-white">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-rose-500/20 rounded-full blur-3xl" />
        <div className="absolute top-1/2 right-1/3 w-64 h-64 bg-amber-500/20 rounded-full blur-3xl" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-6xl font-bold bg-gradient-to-r from-purple-400 via-rose-400 to-amber-400 bg-clip-text text-transparent mb-4">
            Play Mode
          </h1>
          <p className="text-lg md:text-xl text-white/70 max-w-md mx-auto">
            Quick, shareable experiences that reveal something about you
          </p>
        </div>

        {/* Game Cards */}
        <div className="w-full max-w-2xl space-y-4">
          {/* Hometown Crush - Featured */}
          <GameCard
            title="Hometown Crush"
            tagline="Discover your romantic trope"
            description="You're back in your hometown. You didn't expect to see them here. A 7-turn conversation reveals if you're a Slow Burn, All In, or something else."
            gradient="from-amber-500/20 to-rose-500/20"
            borderColor="amber"
            featured
            onClick={() => router.push("/play/hometown-crush")}
          />

          {/* Flirt Test */}
          <GameCard
            title="Flirt Test"
            tagline="What's your flirt style?"
            description="Chat with someone new and discover your natural flirting archetype. Are you bold, playful, or mysterious?"
            gradient="from-rose-500/20 to-purple-500/20"
            borderColor="rose"
            onClick={() => router.push("/play/flirt-test")}
          />
        </div>

        {/* Info */}
        <div className="mt-12 text-center text-white/50 text-sm max-w-md">
          <p>
            Each experience takes about 2 minutes. Share your results and compare with friends.
          </p>
        </div>

        {/* Footer */}
        <div className="mt-8 text-white/30 text-xs">
          <a href="/" className="hover:text-white/50 transition-colors">
            ep-0.com — Interactive AI Episodes
          </a>
        </div>
      </div>
    </div>
  );
}

interface GameCardProps {
  title: string;
  tagline: string;
  description: string;
  gradient: string;
  borderColor: "amber" | "rose" | "purple";
  featured?: boolean;
  onClick: () => void;
}

function GameCard({
  title,
  tagline,
  description,
  gradient,
  borderColor,
  featured,
  onClick,
}: GameCardProps) {
  const borderStyles = {
    amber: "border-amber-400/50 hover:border-amber-400",
    rose: "border-rose-400/50 hover:border-rose-400",
    purple: "border-purple-400/50 hover:border-purple-400",
  };

  const buttonStyles = {
    amber: "from-amber-500 to-rose-500 hover:from-amber-400 hover:to-rose-400",
    rose: "from-rose-500 to-purple-500 hover:from-rose-400 hover:to-purple-400",
    purple: "from-purple-500 to-indigo-500 hover:from-purple-400 hover:to-indigo-400",
  };

  return (
    <div
      className={cn(
        "relative p-6 rounded-2xl backdrop-blur-xl border transition-all cursor-pointer group",
        "bg-gradient-to-br",
        gradient,
        borderStyles[borderColor],
        featured && "ring-2 ring-white/10"
      )}
      onClick={onClick}
    >
      {featured && (
        <div className="absolute -top-3 left-6 px-3 py-1 bg-gradient-to-r from-amber-500 to-rose-500 rounded-full text-xs font-semibold">
          New
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex-1">
          <h2 className="text-2xl font-bold mb-1">{title}</h2>
          <p className="text-white/60 text-sm mb-2">{tagline}</p>
          <p className="text-white/80 text-sm leading-relaxed">{description}</p>
        </div>

        <Button
          className={cn(
            "px-6 py-5 rounded-full font-semibold transition-all",
            "bg-gradient-to-r",
            buttonStyles[borderColor],
            "group-hover:shadow-lg"
          )}
        >
          Play
        </Button>
      </div>
    </div>
  );
}
