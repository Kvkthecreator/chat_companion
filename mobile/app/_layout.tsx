/**
 * Root Layout
 * Handles auth state, deep linking, and navigation structure
 */

import { useEffect, useState } from "react";
import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import * as Linking from "expo-linking";
import * as SplashScreen from "expo-splash-screen";
import { Session } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase/client";
import { api, User } from "../lib/api/client";
import {
  registerForPushNotifications,
  setupNotificationListeners,
  getLastNotificationResponse,
} from "../lib/push/notifications";

// Keep the splash screen visible while we check auth
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const router = useRouter();
  const segments = useSegments();
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Handle authentication state
  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      setSession(session);

      // If logged in, check onboarding status
      if (session) {
        try {
          const userData = await api.users.me();
          setUser(userData);
        } catch (error) {
          console.error("Failed to fetch user:", error);
        }
      }

      setIsLoading(false);
      SplashScreen.hideAsync();
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setSession(session);

      if (session) {
        try {
          const userData = await api.users.me();
          setUser(userData);
        } catch (error) {
          console.error("Failed to fetch user:", error);
        }
      } else {
        setUser(null);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  // Handle navigation based on auth and onboarding state
  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === "(auth)";
    const inOnboardingGroup = segments[0] === "(onboarding)";
    const inMainGroup = segments[0] === "(main)";

    if (!session && !inAuthGroup) {
      // Not logged in, redirect to login
      router.replace("/(auth)/login");
    } else if (session && inAuthGroup) {
      // Logged in but in auth group, check onboarding
      if (user && !user.onboarding_completed_at) {
        router.replace("/(onboarding)");
      } else {
        router.replace("/(main)");
      }
    } else if (session && user && !user.onboarding_completed_at && !inOnboardingGroup) {
      // Logged in but onboarding not complete
      router.replace("/(onboarding)");
    }
  }, [session, user, segments, isLoading]);

  // Set up push notifications when logged in
  useEffect(() => {
    if (!session) return;

    // Register for push notifications
    registerForPushNotifications();

    // Handle notification interactions
    const cleanup = setupNotificationListeners(
      (notification) => {
        // Notification received while app is in foreground
        console.log("Notification received:", notification.request.content.title);
      },
      (response) => {
        // User tapped on notification
        const data = response.notification.request.content.data;
        handleNotificationNavigation(data);
      }
    );

    // Check if app was opened from a notification
    getLastNotificationResponse().then((response) => {
      if (response) {
        const data = response.notification.request.content.data;
        handleNotificationNavigation(data);
      }
    });

    return cleanup;
  }, [session]);

  // Handle deep links
  useEffect(() => {
    const handleDeepLink = ({ url }: { url: string }) => {
      const { path, queryParams } = Linking.parse(url);

      if (path === "chat" && queryParams?.conversation_id) {
        router.push(`/(main)/chat/${queryParams.conversation_id}`);
      } else if (path === "subscription/success") {
        router.push("/(main)/settings?subscribed=true");
      } else if (path === "memory") {
        router.push("/(main)/memory");
      }
    };

    const subscription = Linking.addEventListener("url", handleDeepLink);

    // Check if app was opened with a deep link
    Linking.getInitialURL().then((url) => {
      if (url) {
        handleDeepLink({ url });
      }
    });

    return () => subscription.remove();
  }, []);

  // Navigate based on notification data
  const handleNotificationNavigation = (data: Record<string, unknown>) => {
    if (data?.conversation_id) {
      router.push(`/(main)/chat/${data.conversation_id}`);
    } else if (data?.type === "daily-checkin") {
      // Start new conversation for daily check-in
      router.push("/(main)/chat");
    }
  };

  if (isLoading) {
    return null; // Splash screen is still visible
  }

  return (
    <>
      <StatusBar style="auto" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(onboarding)" />
        <Stack.Screen name="(main)" />
      </Stack>
    </>
  );
}
