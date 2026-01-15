"use client";

import { useEffect, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import { api } from "@/lib/api/client";

const GUEST_SESSION_KEY = "ep0_guest_session_id";

/**
 * Global component that handles guest session conversion after signup.
 *
 * This runs on every page load and checks if:
 * 1. User is authenticated
 * 2. There's a guest session in localStorage
 *
 * If both conditions are met, it converts the guest session to the user's account.
 * This ensures conversion happens even if user doesn't land back on ChatContainer.
 */
export function GuestSessionConverter() {
  const hasAttemptedConversion = useRef(false);

  useEffect(() => {
    // Only attempt conversion once per page load
    if (hasAttemptedConversion.current) return;

    const checkAndConvert = async () => {
      // Check if there's a guest session to convert
      const stored = localStorage.getItem(GUEST_SESSION_KEY);
      if (!stored) return;

      let guestSessionId: string;
      try {
        const data = JSON.parse(stored);
        guestSessionId = data.guest_session_id;
        if (!guestSessionId) return;
      } catch {
        return;
      }

      // Check if user is authenticated
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      // User is authenticated and has a guest session - convert it
      hasAttemptedConversion.current = true;

      try {
        await api.episodes.convertGuest(guestSessionId);
        localStorage.removeItem(GUEST_SESSION_KEY);
        console.log("Guest session converted successfully");
      } catch (err) {
        console.error("Failed to convert guest session:", err);
        // Clear the guest session even on error to prevent repeated attempts
        localStorage.removeItem(GUEST_SESSION_KEY);
      }
    };

    checkAndConvert();
  }, []);

  // This component doesn't render anything
  return null;
}
