"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@/lib/supabase/clients";
import { SessionContextProvider } from "@supabase/auth-helpers-react";
import YarnSpinner from "@/components/ui/OrganicSpinner";

const supabase = createBrowserClient();

/**
 * OAuth Callback Handler
 * 
 * Handles OAuth redirects from providers (Google, etc.)
 * Supabase auth-helpers automatically process the callback and create session cookies.
 * 
 * CRITICAL: Uses createBrowserClient() which stores sessions in COOKIES (not localStorage)
 * to ensure server-side code can read the session.
 */
export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const handleCallback = async () => {
      // Supabase auth-helpers automatically handle OAuth callback
      // Session is already created in cookies by the time we get here
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();
      
      if (sessionError || !session) {
        console.error("OAuth callback failed:", sessionError);
        router.replace("/login");
        return;
      }

      // Verify user is authenticated
      const { data: { user }, error: userError } = await supabase.auth.getUser();

      if (userError || !user) {
        console.error("User verification failed:", userError);
        router.replace("/login");
        return;
      }

      // Get stored redirect path or default to baskets index
      const redirectPath =
        (typeof window !== "undefined" && localStorage.getItem("redirectPath")) ||
        "/dashboard";

      console.log('[Auth Callback] Redirect path from localStorage:', redirectPath);

      if (typeof window !== "undefined") {
        localStorage.removeItem("redirectPath");
      }

      // Full page redirect ensures cookies are sent with the request
      console.log('[Auth Callback] Redirecting to:', redirectPath);
      window.location.href = redirectPath;
    };

    handleCallback();
  }, [router]);

  return (
    <SessionContextProvider supabaseClient={supabase}>
      <div className="min-h-screen w-full flex flex-col justify-center items-center px-4">
        <div className="w-full max-w-sm bg-card border rounded-xl shadow-sm px-6 py-8 space-y-6">
          <div className="text-center space-y-6">
            <YarnSpinner size="lg" className="mx-auto" />
            <div className="space-y-2">
              <h1 className="text-xl font-semibold text-foreground">
                Welcome
              </h1>
              <p className="text-sm text-muted-foreground">
                Redirecting you to your workspace...
              </p>
            </div>
          </div>
        </div>
      </div>
    </SessionContextProvider>
  );
}
