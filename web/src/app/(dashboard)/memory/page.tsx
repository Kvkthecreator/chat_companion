"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  api,
  User,
  FullMemory,
  ThreadSummary,
  FollowUpSummary,
  FactItem,
  PatternItem,
} from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  ChevronLeft,
  Target,
  HelpCircle,
  User as UserIcon,
  Lightbulb,
  Trash2,
  Check,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

export default function MemoryPage() {
  const [user, setUser] = useState<User | null>(null);
  const [memory, setMemory] = useState<FullMemory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [expandedThreads, setExpandedThreads] = useState<Set<string>>(new Set());

  useEffect(() => {
    const loadData = async () => {
      try {
        const [userData, memoryData] = await Promise.all([
          api.users.me(),
          api.memory.getFull(),
        ]);
        setUser(userData);
        setMemory(memoryData);
      } catch (err) {
        console.error("Failed to load memory:", err);
        setError("Failed to load memory data");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await api.memory.deleteItem(id);
      // Refresh memory data
      const memoryData = await api.memory.getFull();
      setMemory(memoryData);
    } catch (err) {
      console.error("Failed to delete:", err);
    }
    setDeleteId(null);
  };

  const handleResolveThread = async (threadId: string) => {
    try {
      await api.memory.resolveThread(threadId);
      // Refresh memory data
      const memoryData = await api.memory.getFull();
      setMemory(memoryData);
    } catch (err) {
      console.error("Failed to resolve thread:", err);
    }
  };

  const toggleThread = (threadId: string) => {
    setExpandedThreads((prev) => {
      const next = new Set(prev);
      if (next.has(threadId)) {
        next.delete(threadId);
      } else {
        next.add(threadId);
      }
      return next;
    });
  };

  if (isLoading) {
    return <MemorySkeleton />;
  }

  if (error || !memory || !user) {
    return (
      <div className="mx-auto max-w-2xl pb-20 md:pb-0">
        <div className="mb-6 flex items-center gap-3">
          <Link href="/dashboard">
            <Button variant="ghost" size="icon">
              <ChevronLeft className="h-5 w-5" />
            </Button>
          </Link>
          <h1 className="text-2xl font-semibold">Memory</h1>
        </div>
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">
              {error || "Failed to load memory data"}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const companionName = user.companion_name || "Your companion";

  return (
    <div className="mx-auto max-w-2xl pb-20 md:pb-0">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <Link href="/dashboard">
          <Button variant="ghost" size="icon">
            <ChevronLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-semibold">
            What {companionName} Remembers
          </h1>
          <p className="text-sm text-muted-foreground">
            Everything {companionName} is paying attention to
          </p>
        </div>
      </div>

      {/* Active Threads */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-4 w-4" />
            Active Threads
          </CardTitle>
        </CardHeader>
        <CardContent>
          {memory.threads.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No active threads. As we chat about things happening in your life,
              I'll keep track of them here.
            </p>
          ) : (
            <div className="space-y-3">
              {memory.threads.map((thread) => (
                <ThreadCard
                  key={thread.id}
                  thread={thread}
                  isExpanded={expandedThreads.has(thread.id)}
                  onToggle={() => toggleThread(thread.id)}
                  onResolve={() => handleResolveThread(thread.id)}
                  onDelete={() => setDeleteId(thread.id)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pending Follow-ups */}
      {memory.follow_ups.length > 0 && (
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <HelpCircle className="h-4 w-4" />
              Things to Follow Up On
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {memory.follow_ups.map((followUp) => (
                <FollowUpCard
                  key={followUp.id}
                  followUp={followUp}
                  onDelete={() => setDeleteId(followUp.id)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Facts by Category */}
      {Object.keys(memory.facts).length > 0 && (
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <UserIcon className="h-4 w-4" />
              Things I Know About You
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(memory.facts).map(([category, facts]) => (
                <FactGroup
                  key={category}
                  category={category}
                  facts={facts}
                  onDelete={(id) => setDeleteId(id)}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Patterns */}
      {memory.patterns.length > 0 && (
        <Card className="mb-6">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Lightbulb className="h-4 w-4" />
              Patterns I've Noticed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-sm text-muted-foreground">
              These are observations, not facts. They help me know when to check
              in differently.
            </p>
            <ul className="space-y-2">
              {memory.patterns.map((pattern) => (
                <li
                  key={pattern.id}
                  className="flex items-start gap-2 text-sm"
                >
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                  <span>{pattern.description}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this memory?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. {companionName} will no longer
              remember this information.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteId && handleDelete(deleteId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function ThreadCard({
  thread,
  isExpanded,
  onToggle,
  onResolve,
  onDelete,
}: {
  thread: ThreadSummary;
  isExpanded: boolean;
  onToggle: () => void;
  onResolve: () => void;
  onDelete: () => void;
}) {
  const isResolved = thread.status === "resolved";

  return (
    <div className="rounded-lg border border-border p-3">
      <div className="flex items-start justify-between gap-2">
        <button
          onClick={onToggle}
          className="flex flex-1 items-start gap-2 text-left"
        >
          {isExpanded ? (
            <ChevronDown className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
          )}
          <div>
            <p className="font-medium">{formatTopic(thread.topic)}</p>
            <p className="text-sm text-muted-foreground">{thread.summary}</p>
          </div>
        </button>
        <div className="flex items-center gap-1">
          {!isResolved && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={onResolve}
              title="Mark as resolved"
            >
              <Check className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-muted-foreground hover:text-destructive"
            onClick={onDelete}
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {isExpanded && thread.key_details.length > 0 && (
        <div className="mt-3 pl-6">
          <p className="mb-1 text-xs font-medium text-muted-foreground">
            Details:
          </p>
          <ul className="space-y-1">
            {thread.key_details.map((detail, i) => (
              <li key={i} className="text-sm text-muted-foreground">
                • {detail}
              </li>
            ))}
          </ul>
        </div>
      )}

      {isResolved && (
        <div className="mt-2 pl-6">
          <span className="text-xs text-muted-foreground">Resolved</span>
        </div>
      )}
    </div>
  );
}

function FollowUpCard({
  followUp,
  onDelete,
}: {
  followUp: FollowUpSummary;
  onDelete: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-2 rounded-lg border border-border p-3">
      <div>
        <p className="text-sm font-medium">{followUp.question}</p>
        <p className="text-xs text-muted-foreground">{followUp.context}</p>
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
        onClick={onDelete}
        title="Delete"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}

function FactGroup({
  category,
  facts,
  onDelete,
}: {
  category: string;
  facts: FactItem[];
  onDelete: (id: string) => void;
}) {
  return (
    <div>
      <p className="mb-2 text-sm font-medium capitalize">{category}</p>
      <ul className="space-y-1.5">
        {facts.map((fact) => (
          <li
            key={fact.id}
            className="group flex items-start justify-between gap-2 text-sm"
          >
            <span className="text-muted-foreground">{fact.value}</span>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
              onClick={() => onDelete(fact.id)}
              title="Delete"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function MemorySkeleton() {
  return (
    <div className="mx-auto max-w-2xl space-y-6 pb-20 md:pb-0">
      <div className="flex items-center gap-3">
        <Skeleton className="h-10 w-10" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
      </div>
      <Skeleton className="h-40 rounded-xl" />
      <Skeleton className="h-32 rounded-xl" />
      <Skeleton className="h-48 rounded-xl" />
    </div>
  );
}

function formatTopic(topic: string): string {
  return topic.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
