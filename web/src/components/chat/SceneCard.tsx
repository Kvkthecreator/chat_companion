"use client";

import { useState } from "react";
import { Star, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api/client";
import type { EpisodeImage, SceneGenerateResponse, VisualType } from "@/types";

interface SceneCardProps {
  scene: EpisodeImage | SceneGenerateResponse;
  visualType?: VisualType;
  onMemoryToggle?: (isMemory: boolean) => void;
}

/**
 * SceneCard - Renders visual moments in chat (character, object, atmosphere images)
 *
 * Design philosophy:
 * - Full-width cinematic cards that break the chat flow
 * - Larger aspect ratio (4:3) for more visual impact than tiny 16:9
 * - Consistent styling with InstructionCard for cohesive "moment" feel
 * - Memory save functionality for user-curated gallery
 */
export function SceneCard({ scene, visualType = "character", onMemoryToggle }: SceneCardProps) {
  const [isMemory, setIsMemory] = useState(
    "is_memory" in scene ? scene.is_memory : false
  );
  const [isSaving, setIsSaving] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const episodeImageId = "id" in scene ? scene.id : null;

  const handleToggleMemory = async () => {
    if (!episodeImageId || isSaving) return;

    setIsSaving(true);
    try {
      const updated = await api.scenes.toggleMemory(episodeImageId, !isMemory);
      setIsMemory(updated.is_memory);
      onMemoryToggle?.(updated.is_memory);
    } catch (error) {
      console.error("Failed to toggle memory:", error);
    } finally {
      setIsSaving(false);
    }
  };

  // Visual type affects subtle styling cues
  const isAtmosphere = visualType === "atmosphere";
  const isObject = visualType === "object";

  return (
    <div className="my-6 w-full">
      <div className={cn(
        "relative overflow-hidden rounded-2xl shadow-2xl",
        "ring-1 ring-white/20",
        // Subtle glow effect for visual impact
        "shadow-black/40"
      )}>
        {/* Image - 4:3 aspect for more visual presence */}
        <div className={cn(
          "relative",
          isObject ? "aspect-square" : "aspect-[4/3]"
        )}>
          {/* Loading state */}
          {!imageLoaded && !imageError && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-10 w-10 animate-spin text-white/70" />
                <p className="text-sm text-white/60">Loading scene...</p>
              </div>
            </div>
          )}

          {/* Error state */}
          {imageError ? (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm">
              <p className="text-sm text-white/80">Failed to load image</p>
            </div>
          ) : (
            <img
              src={scene.image_url}
              alt={scene.caption || "Scene"}
              className={cn(
                "h-full w-full object-cover transition-all duration-700",
                imageLoaded ? "opacity-100 scale-100" : "opacity-0 scale-105"
              )}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />
          )}

          {/* Cinematic gradient overlay - stronger at bottom for UI elements */}
          <div className={cn(
            "absolute inset-0",
            isAtmosphere
              ? "bg-gradient-to-t from-black/50 via-transparent to-black/20"
              : "bg-gradient-to-t from-black/70 via-black/10 to-black/5"
          )} />

          {/* Visual type indicator (subtle) */}
          {(isObject || isAtmosphere) && (
            <div className="absolute top-3 left-3">
              <span className="px-2 py-1 rounded-full text-[10px] font-medium uppercase tracking-wider bg-black/40 text-white/70 backdrop-blur-sm">
                {isObject ? "Detail" : "Atmosphere"}
              </span>
            </div>
          )}
        </div>

        {/* Caption and save button */}
        <div className="absolute bottom-0 left-0 right-0 flex items-end justify-between gap-3 px-4 py-4">
          {/* Caption (if available) */}
          {scene.caption && (
            <p className="text-sm text-white/90 font-medium leading-snug flex-1 drop-shadow-lg">
              {scene.caption}
            </p>
          )}

          {/* Save to memory button */}
          {episodeImageId && (
            <button
              onClick={handleToggleMemory}
              disabled={isSaving}
              className={cn(
                "flex-shrink-0 rounded-full p-3 backdrop-blur-md transition-all",
                "border shadow-lg",
                isMemory
                  ? "bg-amber-500/30 border-amber-400/50 text-amber-300"
                  : "bg-black/50 border-white/20 text-white/80 hover:bg-black/70 hover:text-white"
              )}
              title={isMemory ? "Remove from memories" : "Save as memory"}
            >
              {isSaving ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Star className={cn("h-5 w-5", isMemory && "fill-current")} />
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface SceneCardSkeletonProps {
  caption?: string;
  visualType?: VisualType;
}

/**
 * SceneCardSkeleton - Loading placeholder while image generates
 */
export function SceneCardSkeleton({ caption, visualType = "character" }: SceneCardSkeletonProps) {
  const isObject = visualType === "object";

  return (
    <div className="my-6 w-full">
      <div className={cn(
        "relative overflow-hidden rounded-2xl shadow-2xl",
        "ring-1 ring-white/20",
        "bg-gradient-to-br from-gray-900/80 to-black/90 backdrop-blur-sm"
      )}>
        <div className={cn(
          "relative flex items-center justify-center",
          isObject ? "aspect-square" : "aspect-[4/3]"
        )}>
          {/* Animated gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-pink-900/20 to-blue-900/20 animate-pulse" />

          {/* Content */}
          <div className="relative flex flex-col items-center gap-3 text-white/80">
            <div className="relative">
              <Loader2 className="h-12 w-12 animate-spin text-white/50" />
              <div className="absolute inset-0 h-12 w-12 rounded-full bg-white/10 animate-ping" />
            </div>
            <p className="text-sm font-medium">{caption || "Creating your scene..."}</p>
            <p className="text-xs text-white/50">This may take a moment</p>
          </div>
        </div>
      </div>
    </div>
  );
}
