"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, User, Conversation } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [userData, conversationsData] = await Promise.all([
          api.users.me(),
          api.conversations.list({ limit: 5 }).catch(() => []),
        ]);
        setUser(userData);
        setConversations(conversationsData);
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      }
      setIsLoading(false);
    };

    loadData();
  }, []);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (!user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Failed to load user data</div>
      </div>
    );
  }

  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(":");
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? "PM" : "AM";
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="mx-auto max-w-2xl pb-20 md:pb-0">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            {getGreeting()}, {user.display_name || "there"}
          </h1>
          <p className="text-muted-foreground">
            {user.companion_name} is here for you
          </p>
        </div>
        <Link href="/settings">
          <Button variant="ghost" size="icon">
            <SettingsIcon className="h-5 w-5" />
          </Button>
        </Link>
      </div>

      {/* Companion Card */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-3xl">
              💬
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold">{user.companion_name}</h2>
              <p className="text-sm text-muted-foreground">
                Your {getSupportStyleLabel(user.support_style)}
              </p>
            </div>
            <Button onClick={() => router.push("/chat")}>
              Chat Now
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Schedule Info */}
      <Card className="mb-6">
        <CardContent className="p-6">
          <h3 className="mb-4 font-semibold">Daily Check-in</h3>
          <div className="flex items-center gap-3 text-sm">
            <ClockIcon className="h-5 w-5 text-muted-foreground" />
            <div>
              <p className="font-medium">
                {formatTime(user.preferred_message_time || "09:00")}
              </p>
              <p className="text-muted-foreground">
                {user.timezone || "America/New_York"}
              </p>
            </div>
          </div>
          {!user.telegram_user_id && (
            <div className="mt-4 rounded-lg bg-muted p-3 text-sm">
              <p className="text-muted-foreground">
                Connect Telegram to receive daily messages on your phone.
              </p>
              <Link href="/settings" className="text-primary hover:underline">
                Connect now →
              </Link>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Conversations */}
      {conversations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent Conversations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {conversations.map((conv) => (
                <Link
                  key={conv.id}
                  href={`/chat/${conv.id}`}
                  className="block rounded-lg border border-border p-3 transition-colors hover:bg-muted"
                >
                  <div className="flex items-center justify-between">
                    <div className="text-sm">
                      <p className="font-medium">
                        {formatDate(conv.started_at)}
                      </p>
                      <p className="text-muted-foreground">
                        {conv.message_count} messages
                      </p>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {conv.channel}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty state */}
      {conversations.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">
              No conversations yet. Start chatting with {user.companion_name}!
            </p>
            <Button onClick={() => router.push("/chat")} className="mt-4">
              Start a Conversation
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
        <Skeleton className="h-10 w-10 rounded-full" />
      </div>
      <Skeleton className="h-28 rounded-xl" />
      <Skeleton className="h-32 rounded-xl" />
    </div>
  );
}

function getSupportStyleLabel(style?: string): string {
  switch (style) {
    case "motivational":
      return "Motivational Coach";
    case "friendly_checkin":
      return "Friendly Companion";
    case "accountability":
      return "Accountability Partner";
    case "listener":
      return "Gentle Listener";
    default:
      return "AI Companion";
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function SettingsIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

function ClockIcon({ className }: { className?: string }) {
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
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}
