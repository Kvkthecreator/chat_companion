"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { StreamEpisodeCompleteEvent, FlirtArchetypeEvaluation } from "@/types";

interface EpisodeCompleteModalProps {
  open: boolean;
  onClose: () => void;
  evaluation: StreamEpisodeCompleteEvent["evaluation"];
  nextSuggestion: StreamEpisodeCompleteEvent["next_suggestion"];
  characterId: string;
  characterName: string;
}

/**
 * Modal displayed when Director detects episode completion.
 * Shows evaluation result (e.g., flirt archetype) and next episode CTA.
 */
export function EpisodeCompleteModal({
  open,
  onClose,
  evaluation,
  nextSuggestion,
  characterId,
  characterName,
}: EpisodeCompleteModalProps) {
  const router = useRouter();

  // Parse evaluation result based on type
  const isFlirtArchetype = evaluation?.evaluation_type === "flirt_archetype";
  const flirtResult = isFlirtArchetype
    ? (evaluation?.result as FlirtArchetypeEvaluation)
    : null;

  const handleContinue = () => {
    if (nextSuggestion) {
      // Navigate to next episode
      router.push(`/chat/${characterId}?episode=${nextSuggestion.episode_id}`);
    }
    onClose();
  };

  const handleShare = () => {
    if (evaluation?.share_id) {
      // Copy share URL to clipboard
      const shareUrl = `${window.location.origin}/r/${evaluation.share_id}`;
      navigator.clipboard.writeText(shareUrl);
      // Could show a toast here
    }
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-center text-2xl">
            {isFlirtArchetype ? "Your Flirt Style" : "Episode Complete"}
          </DialogTitle>
          {flirtResult && (
            <DialogDescription className="text-center text-lg font-medium text-primary">
              {flirtResult.title}
            </DialogDescription>
          )}
        </DialogHeader>

        <div className="py-6">
          {flirtResult ? (
            <div className="space-y-4">
              {/* Archetype description */}
              <p className="text-center text-muted-foreground">
                {flirtResult.description}
              </p>

              {/* Confidence indicator */}
              <div className="flex justify-center">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>Confidence:</span>
                  <div className="h-2 w-24 rounded-full bg-muted overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all"
                      style={{ width: `${(flirtResult.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span>{Math.round((flirtResult.confidence || 0) * 100)}%</span>
                </div>
              </div>

              {/* Primary signals */}
              {flirtResult.primary_signals && flirtResult.primary_signals.length > 0 && (
                <div className="flex flex-wrap justify-center gap-2">
                  {flirtResult.primary_signals.map((signal, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 text-xs rounded-full bg-primary/10 text-primary"
                    >
                      {signal.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-center text-muted-foreground">
              You&apos;ve completed this episode with {characterName}.
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-3">
          {evaluation?.share_id && (
            <Button variant="outline" onClick={handleShare} className="w-full">
              Share Result
            </Button>
          )}

          {nextSuggestion && (
            <Button onClick={handleContinue} className="w-full">
              Continue with {characterName}
            </Button>
          )}

          <Button variant="ghost" onClick={onClose} className="w-full">
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
