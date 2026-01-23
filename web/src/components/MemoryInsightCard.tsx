"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { api, MemorySummary } from "@/lib/api/client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Target, HelpCircle, ChevronRight } from "lucide-react";

interface MemoryInsightCardProps {
  companionName: string;
}

export function MemoryInsightCard({ companionName }: MemoryInsightCardProps) {
  const [memory, setMemory] = useState<MemorySummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMemory = async () => {
      try {
        const data = await api.memory.getSummary();
        setMemory(data);
      } catch (err) {
        console.error("Failed to load memory summary:", err);
        setError("Failed to load");
      } finally {
        setIsLoading(false);
      }
    };

    loadMemory();
  }, []);

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <Skeleton className="h-5 w-48" />
        </CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-2/3" />
        </CardContent>
      </Card>
    );
  }

  if (error || !memory) {
    return null; // Silently fail - this card is optional
  }

  const hasContent =
    memory.active_threads.length > 0 || memory.pending_follow_ups.length > 0;

  if (!hasContent) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium">
            What {companionName} is paying attention to
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No active threads yet. As we chat, I'll keep track of what's going
            on in your life.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-medium">
          What {companionName} is paying attention to
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Active Threads */}
        {memory.active_threads.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <Target className="h-4 w-4" />
              <span>Active threads</span>
            </div>
            <ul className="space-y-1.5 pl-6">
              {memory.active_threads.slice(0, 3).map((thread) => (
                <li
                  key={thread.id}
                  className="text-sm text-foreground"
                >
                  <span className="font-medium">
                    {formatTopic(thread.topic)}
                  </span>
                  {thread.summary && (
                    <span className="text-muted-foreground">
                      {" "}
                      - {truncate(thread.summary, 50)}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Pending Follow-ups */}
        {memory.pending_follow_ups.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
              <HelpCircle className="h-4 w-4" />
              <span>Things to follow up on</span>
            </div>
            <ul className="space-y-1.5 pl-6">
              {memory.pending_follow_ups.slice(0, 2).map((followUp) => (
                <li
                  key={followUp.id}
                  className="text-sm text-foreground"
                >
                  {followUp.question}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Link to full memory page */}
        <Link
          href="/companion"
          className="flex items-center gap-1 text-sm text-primary hover:underline"
        >
          See all
          <ChevronRight className="h-4 w-4" />
        </Link>
      </CardContent>
    </Card>
  );
}

function formatTopic(topic: string): string {
  return topic
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + "...";
}
