"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { MemoryEvent } from "@/types";

const memoryTypeColors: Record<string, string> = {
  fact: "bg-blue-500/10 text-blue-500",
  preference: "bg-green-500/10 text-green-500",
  event: "bg-purple-500/10 text-purple-500",
  goal: "bg-yellow-500/10 text-yellow-600",
  relationship: "bg-pink-500/10 text-pink-500",
  emotion: "bg-orange-500/10 text-orange-500",
};

export default function MemoriesPage() {
  const [memories, setMemories] = useState<MemoryEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const memoriesData = await api.memory.list({ limit: 50 });
        setMemories(memoriesData);
      } catch (err) {
        console.error("Failed to load memories:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="grid gap-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Memories</h1>
        <p className="text-muted-foreground">
          Everything your characters remember about you
        </p>
      </div>

      {memories.length === 0 ? (
        <Card className="py-12">
          <CardContent className="flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white text-2xl mb-4">
              &#x2764;
            </div>
            <h3 className="text-lg font-semibold mb-2">No memories yet</h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Start chatting with your characters and they&apos;ll begin remembering things about you.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3">
          {memories.map((memory) => (
            <Card key={memory.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1 flex-1">
                    <CardTitle className="text-base font-medium">
                      {memory.summary}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {new Date(memory.created_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </CardDescription>
                  </div>
                  <Badge
                    variant="secondary"
                    className={memoryTypeColors[memory.type] || ""}
                  >
                    {memory.type}
                  </Badge>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
