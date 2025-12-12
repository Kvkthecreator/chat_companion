"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api/client";
import { useUser } from "./useUser";

export function useSubscription() {
  const { user, reload } = useUser();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const isPremium = user?.subscription_status === "premium";
  const expiresAt = user?.subscription_expires_at;

  const upgrade = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { checkout_url } = await api.subscription.createCheckout();
      // Redirect to Lemon Squeezy checkout
      window.location.href = checkout_url;
    } catch (err) {
      setError(err as Error);
      setIsLoading(false);
      throw err;
    }
    // Don't set loading false - we're redirecting
  }, []);

  const manageSubscription = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { portal_url } = await api.subscription.getPortal();
      // Open portal in new tab
      window.open(portal_url, "_blank");
    } catch (err) {
      setError(err as Error);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isPremium,
    expiresAt,
    user,
    upgrade,
    manageSubscription,
    isLoading,
    error,
    reload,
  };
}
