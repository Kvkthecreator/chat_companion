"use client";

import { useState } from "react";
import { ThreadSummary } from "@/lib/api/client";

const DOMAIN_ICONS: Record<string, string> = {
  career: "💼",
  location: "📍",
  relationships: "💕",
  health: "🏥",
  creative: "🚀",
  life_stage: "🎓",
  personal: "💭",
};

const DOMAIN_LABELS: Record<string, string> = {
  career: "Career",
  location: "Location",
  relationships: "Relationships",
  health: "Health",
  creative: "Creative",
  life_stage: "Life Stage",
  personal: "Personal",
};

function formatPhase(phase: string): string {
  return phase
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

interface ThreadChipProps {
  thread: ThreadSummary;
  onClick?: () => void;
}

function ThreadChip({ thread, onClick }: ThreadChipProps) {
  const domainIcon = thread.domain ? DOMAIN_ICONS[thread.domain] : "📌";
  const phaseLabel = thread.phase ? ` (${formatPhase(thread.phase)})` : "";

  // Truncate summary if too long
  const displayName =
    thread.summary.length > 30
      ? thread.summary.substring(0, 27) + "..."
      : thread.summary;

  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full text-xs hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      title={thread.summary + phaseLabel}
    >
      <span>{domainIcon}</span>
      <span className="text-gray-700 dark:text-gray-300">
        {displayName}
        {phaseLabel && (
          <span className="text-gray-500 dark:text-gray-400">{phaseLabel}</span>
        )}
      </span>
    </button>
  );
}

interface ThreadContextHeaderProps {
  threads: ThreadSummary[];
  maxVisible?: number;
  onThreadClick?: (threadId: string) => void;
  className?: string;
}

export function ThreadContextHeader({
  threads,
  maxVisible = 3,
  onThreadClick,
  className = "",
}: ThreadContextHeaderProps) {
  const [expanded, setExpanded] = useState(false);

  // Sort by priority weight (higher first) then by recency
  const sortedThreads = [...threads].sort((a, b) => {
    const weightDiff = (b.priority_weight || 1) - (a.priority_weight || 1);
    if (weightDiff !== 0) return weightDiff;
    // Fall back to updated_at if available
    if (a.updated_at && b.updated_at) {
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    }
    return 0;
  });

  const activeThreads = sortedThreads.filter((t) => t.status === "active");
  const visibleThreads = expanded ? activeThreads : activeThreads.slice(0, maxVisible);
  const hiddenCount = activeThreads.length - maxVisible;

  if (activeThreads.length === 0) {
    return null;
  }

  return (
    <div
      className={`border-b border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50 px-4 py-2 ${className}`}
    >
      <div className="flex items-center gap-2 text-sm">
        <span className="font-medium text-gray-600 dark:text-gray-400 shrink-0">
          Tracking:
        </span>
        <div className="flex flex-wrap gap-2 items-center">
          {visibleThreads.map((thread) => (
            <ThreadChip
              key={thread.id}
              thread={thread}
              onClick={() => onThreadClick?.(thread.id)}
            />
          ))}
          {!expanded && hiddenCount > 0 && (
            <button
              onClick={() => setExpanded(true)}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-xs font-medium"
            >
              +{hiddenCount} more
            </button>
          )}
          {expanded && hiddenCount > 0 && (
            <button
              onClick={() => setExpanded(false)}
              className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 text-xs"
            >
              Show less
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ThreadContextHeader;
