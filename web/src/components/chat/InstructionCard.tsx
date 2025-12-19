"use client";

import { cn } from "@/lib/utils";

interface InstructionCardProps {
  content: string;
  hasBackground?: boolean;
}

/**
 * InstructionCard - Renders game-like instruction/hint cards in chat
 *
 * Design philosophy:
 * - Consistent card styling with SceneCard (same width, margins, rounded corners)
 * - Game UI feel - like receiving a mission briefing or hint
 * - Styled text that feels special, not just another message
 * - Free (no sparks) - these are narrative helpers, not premium visuals
 *
 * Examples:
 * - "Supply Room - Code: 4721"
 * - "Choice: Tell her the truth / Keep the secret"
 * - "Objective: Find the missing letter before midnight"
 */
export function InstructionCard({ content, hasBackground = false }: InstructionCardProps) {
  // Parse content to detect if it has structured format (key: value pairs, choices, etc.)
  const lines = content.split("\n").filter(Boolean);
  const hasMultipleLines = lines.length > 1;

  // Detect choice format (contains " / " separator)
  const isChoice = content.includes(" / ");
  const choices = isChoice ? content.split(" / ").map(c => c.trim()) : [];

  // Detect key-value format (contains " - " or ": ")
  const isKeyValue = !isChoice && (content.includes(" - ") || /^[A-Za-z]+:/.test(content));

  return (
    <div className="my-6 w-full">
      <div className={cn(
        "relative overflow-hidden rounded-2xl shadow-2xl",
        "ring-1",
        hasBackground
          ? "ring-amber-500/30 bg-gradient-to-br from-amber-950/80 via-black/80 to-amber-950/60"
          : "ring-amber-500/20 bg-gradient-to-br from-amber-950/90 via-gray-900 to-amber-950/70"
      )}>
        {/* Decorative corner accents */}
        <div className="absolute top-0 left-0 w-16 h-16 border-t-2 border-l-2 border-amber-500/30 rounded-tl-2xl" />
        <div className="absolute bottom-0 right-0 w-16 h-16 border-b-2 border-r-2 border-amber-500/30 rounded-br-2xl" />

        {/* Subtle grid pattern overlay for game UI feel */}
        <div className="absolute inset-0 opacity-5 bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:20px_20px]" />

        {/* Content */}
        <div className="relative px-6 py-8">
          {/* Icon/badge */}
          <div className="flex justify-center mb-4">
            <div className="w-10 h-10 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
              <InstructionIcon className="w-5 h-5 text-amber-400" />
            </div>
          </div>

          {/* Main content */}
          {isChoice ? (
            // Choice format - render as buttons/options
            <div className="space-y-3">
              <p className="text-xs uppercase tracking-widest text-amber-500/70 text-center font-medium mb-4">
                Choose your path
              </p>
              {choices.map((choice, i) => (
                <div
                  key={i}
                  className="text-center py-3 px-4 rounded-xl bg-black/30 border border-amber-500/20 text-white/90 text-sm font-medium hover:bg-amber-500/10 hover:border-amber-500/40 transition-colors cursor-default"
                >
                  {choice}
                </div>
              ))}
            </div>
          ) : hasMultipleLines ? (
            // Multi-line format
            <div className="space-y-2 text-center">
              {lines.map((line, i) => (
                <p
                  key={i}
                  className={cn(
                    "font-medium",
                    i === 0
                      ? "text-lg text-white"
                      : "text-sm text-white/70"
                  )}
                >
                  {line}
                </p>
              ))}
            </div>
          ) : isKeyValue ? (
            // Key-value format - highlight the value
            <div className="text-center">
              <p className="text-lg font-bold text-white tracking-wide">
                {content}
              </p>
            </div>
          ) : (
            // Default - centered text
            <p className="text-lg font-medium text-white text-center leading-relaxed">
              {content}
            </p>
          )}

          {/* Subtle hint text */}
          <p className="text-[10px] uppercase tracking-widest text-amber-500/50 text-center mt-6">
            Story hint
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Icon for instruction cards - compass/target feel
 */
function InstructionIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      {/* Crosshair/target icon */}
      <circle cx="12" cy="12" r="10" />
      <line x1="22" y1="12" x2="18" y2="12" />
      <line x1="6" y1="12" x2="2" y2="12" />
      <line x1="12" y1="6" x2="12" y2="2" />
      <line x1="12" y1="22" x2="12" y2="18" />
    </svg>
  );
}
