"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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
import { useUser } from "@/hooks/useUser";
import {
  api,
  FullMemory,
  ThreadSummary,
  FollowUpSummary,
  FactItem,
} from "@/lib/api/client";
import {
  Brain,
  Target,
  HelpCircle,
  User as UserIcon,
  Lightbulb,
  Trash2,
  Check,
  ChevronDown,
  ChevronRight,
  MapPin,
  Heart,
  Briefcase,
  Activity,
  Sparkles,
  BookOpen,
  Users,
  Calendar,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

// Domain icons mapping
const DOMAIN_ICONS: Record<string, typeof Briefcase> = {
  career: Briefcase,
  location: MapPin,
  relationships: Heart,
  health: Activity,
  creative: Sparkles,
  life_stage: BookOpen,
  personal: Users,
};

export default function MemoryPage() {
  const { user } = useUser();
  const [memory, setMemory] = useState<FullMemory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [expandedThreads, setExpandedThreads] = useState<Set<string>>(new Set());

  const companionName = user?.companion_name || "Your Companion";

  const loadMemory = useCallback(async () => {
    try {
      const memoryData = await api.memory.getFull();
      setMemory(memoryData);
    } catch (err) {
      console.error("Failed to load memory:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMemory();
  }, [loadMemory]);

  const handleDelete = async (id: string) => {
    try {
      await api.memory.deleteItem(id);
      await loadMemory();
    } catch (err) {
      console.error("Failed to delete:", err);
    }
    setDeleteId(null);
  };

  const handleResolveThread = async (threadId: string) => {
    try {
      await api.memory.resolveThread(threadId);
      await loadMemory();
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
    return <MemoryPageSkeleton />;
  }

  const activeThreads = memory?.threads.filter(t => t.status !== "resolved") || [];
  const resolvedThreads = memory?.threads.filter(t => t.status === "resolved") || [];

  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-20 md:pb-0">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Brain className="h-8 w-8 text-primary" />
          Memory
        </h1>
        <p className="text-muted-foreground">
          Everything {companionName} remembers about you
        </p>
      </div>

      {/* Active Threads */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-4 w-4" />
            Active Threads
            {activeThreads.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {activeThreads.length}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {activeThreads.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No active threads. As we chat about things happening in your life,
              I'll keep track of them here.
            </p>
          ) : (
            <div className="space-y-3">
              {activeThreads.map((thread) => (
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
      {memory && memory.follow_ups.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <HelpCircle className="h-4 w-4" />
              Things to Follow Up On
              <Badge variant="secondary" className="ml-2">
                {memory.follow_ups.length}
              </Badge>
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
      {memory && Object.keys(memory.facts).length > 0 && (
        <Card>
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
      {memory && memory.patterns.length > 0 && (
        <Card>
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

      {/* Resolved Threads (collapsed by default) */}
      {resolvedThreads.length > 0 && (
        <Card className="border-dashed">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base text-muted-foreground">
              <Check className="h-4 w-4" />
              Resolved Threads
              <Badge variant="outline" className="ml-2">
                {resolvedThreads.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {resolvedThreads.map((thread) => (
                <div
                  key={thread.id}
                  className="flex items-center justify-between gap-2 text-sm text-muted-foreground py-2"
                >
                  <span>{formatTopic(thread.topic)}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 opacity-50 hover:opacity-100"
                    onClick={() => setDeleteId(thread.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
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
  const DomainIcon = thread.domain ? DOMAIN_ICONS[thread.domain] || Target : Target;

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
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <DomainIcon className="h-4 w-4 text-primary shrink-0" />
              <p className="font-medium truncate">{formatTopic(thread.topic)}</p>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5">{thread.summary}</p>
            {thread.domain && (
              <div className="flex items-center gap-2 mt-2">
                <Badge variant="secondary" className="text-xs capitalize">
                  {thread.domain.replace(/_/g, " ")}
                </Badge>
                {thread.phase && (
                  <Badge variant="outline" className="text-xs capitalize">
                    {thread.phase.replace(/_/g, " ")}
                  </Badge>
                )}
              </div>
            )}
          </div>
        </button>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={onResolve}
            title="Mark as resolved"
          >
            <Check className="h-4 w-4" />
          </Button>
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

      {isExpanded && (
        <div className="mt-3 pl-6 space-y-3">
          {thread.key_details.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Details:</p>
              <ul className="space-y-1">
                {thread.key_details.map((detail, i) => (
                  <li key={i} className="text-sm text-muted-foreground">
                    • {detail}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {thread.follow_up_date && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Calendar className="h-3.5 w-3.5" />
              Follow up: {formatDistanceToNow(new Date(thread.follow_up_date), { addSuffix: true })}
            </div>
          )}

          {thread.updated_at && (
            <div className="text-xs text-muted-foreground/70">
              Last updated: {formatDistanceToNow(new Date(thread.updated_at), { addSuffix: true })}
            </div>
          )}
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
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{followUp.question}</p>
        <p className="text-xs text-muted-foreground mt-1">{followUp.context}</p>
        {followUp.follow_up_date && (
          <div className="flex items-center gap-1.5 mt-2 text-xs text-muted-foreground">
            <Calendar className="h-3 w-3" />
            {formatDistanceToNow(new Date(followUp.follow_up_date), { addSuffix: true })}
          </div>
        )}
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

function MemoryPageSkeleton() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-20 md:pb-0">
      <div className="space-y-2">
        <Skeleton className="h-9 w-48" />
        <Skeleton className="h-5 w-64" />
      </div>
      <Skeleton className="h-48 rounded-xl" />
      <Skeleton className="h-32 rounded-xl" />
      <Skeleton className="h-40 rounded-xl" />
    </div>
  );
}

function formatTopic(topic: string): string {
  return topic.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}
