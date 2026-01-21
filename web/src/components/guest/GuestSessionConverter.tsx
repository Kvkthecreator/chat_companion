"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase/client";

/**
 * GuestSessionConverter
 *
 * Handles converting guest sessions to authenticated sessions.
 * This component runs on mount and checks if there's a guest session
 * that needs to be merged with a newly authenticated user.
 */
export function GuestSessionConverter() {
  useEffect(() => {
    const supabase = createClient();

    // Listen for auth state changes to handle guest conversion
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === "SIGNED_IN" && session?.user) {
          // Check for guest session in localStorage
          const guestSessionId = localStorage.getItem("guest_session_id");

          if (guestSessionId) {
            try {
              // Could call an API to merge guest data with authenticated user
              // For now, just clear the guest session
              localStorage.removeItem("guest_session_id");
            } catch (error) {
              console.error("Failed to convert guest session:", error);
            }
          }
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // This component doesn't render anything
  return null;
}
