"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { MessageCircle, Settings, Bell, Clock } from "lucide-react";
import Link from "next/link";

interface User {
  id: string;
  display_name?: string;
  timezone?: string;
  preferred_message_time?: string;
  companion_name?: string;
  created_at: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const supabase = createClient();

  useEffect(() => {
    async function loadData() {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
          router.push("/login");
          return;
        }

        // TODO: Load user data from API
        // For now, just set basic data from session
        setUser({
          id: session.user.id,
          display_name: session.user.user_metadata?.full_name || session.user.email?.split("@")[0],
          created_at: session.user.created_at,
        });
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [router, supabase.auth]);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // Check if onboarding is complete
  const needsOnboarding = !user?.companion_name;

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {user?.display_name ? `Welcome, ${user.display_name}` : "Welcome"}
        </h1>
        <p className="text-muted-foreground">
          Your companion is here for you.
        </p>
      </div>

      {/* Onboarding CTA */}
      {needsOnboarding && (
        <Card className="border-primary/50 bg-primary/5">
          <CardHeader>
            <CardTitle>Complete Your Setup</CardTitle>
            <CardDescription>
              Set up your companion to start receiving daily messages.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/onboarding">Get Started</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Next Message</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {user?.preferred_message_time || "Not set"}
            </div>
            <p className="text-xs text-muted-foreground">
              {user?.timezone || "Set your timezone"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Your Companion</CardTitle>
            <MessageCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {user?.companion_name || "Not named yet"}
            </div>
            <p className="text-xs text-muted-foreground">
              Ready to chat anytime
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Notifications</CardTitle>
            <Bell className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Telegram</div>
            <p className="text-xs text-muted-foreground">
              Primary channel
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button asChild variant="outline">
            <Link href="/chat">
              <MessageCircle className="h-4 w-4 mr-2" />
              Chat Now
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/settings">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-48 rounded-xl" />
    </div>
  );
}
