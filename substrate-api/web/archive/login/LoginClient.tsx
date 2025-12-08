"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createBrowserClient } from "@/lib/supabase/clients";
import { Button } from "@/components/ui/Button";
import Brand from "@/components/Brand";

const supabase = createBrowserClient();

export default function LoginClient() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const showDevMagicLogin = process.env.NODE_ENV === "development";

  // Check if user is already logged in and redirect if so
  useEffect(() => {
    const checkSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();

      if (session) {
        console.log('[Login] User already logged in, redirecting...');
        const redirectPath = localStorage.getItem('redirectPath') || '/dashboard';
        console.log('[Login] Redirecting to:', redirectPath);
        localStorage.removeItem('redirectPath');
        window.location.href = redirectPath;
      }
    };

    checkSession();
  }, []);

  // Store return_to in localStorage if present (for MCP OAuth flow)
  useEffect(() => {
    const returnTo = searchParams.get('return_to');
    console.log('[Login] return_to from query params:', returnTo);
    console.log('[Login] All search params:', Object.fromEntries(searchParams.entries()));
    if (returnTo) {
      console.log('[Login] Storing redirectPath in localStorage:', returnTo);
      localStorage.setItem('redirectPath', returnTo);
      // Verify it was stored
      const stored = localStorage.getItem('redirectPath');
      console.log('[Login] Verified localStorage.redirectPath:', stored);
    } else {
      console.log('[Login] No return_to parameter found');
      // Check if we have a stored path from previous visit
      const existing = localStorage.getItem('redirectPath');
      console.log('[Login] Existing redirectPath in localStorage:', existing);
    }
  }, [searchParams]);

  const resolveRedirectUrl = () => {
    if (typeof window !== "undefined") {
      return `${window.location.origin}/auth/callback`;
    }
    const fallback = process.env.NEXT_PUBLIC_SITE_URL ?? "https://www.yarnnn.com";
    return `${fallback.replace(/\/$/, "")}/auth/callback`;
  };

  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: resolveRedirectUrl(),
      },
    });
    if (error) console.error("Google login error:", error.message);
  };

  const handleMagicLinkLogin = async () => {
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        shouldCreateUser: false,
        emailRedirectTo: resolveRedirectUrl(),
      },
    });
    if (error) setErrorMsg(error.message);
    else setSent(true);
  };

  return (
    <div className="flex flex-col items-center space-y-4">
      <Brand />
      <Button onClick={handleGoogleLogin} className="w-full">Continue with Google</Button>
      {showDevMagicLogin && (
        <div className="w-full space-y-3">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="border rounded-md p-2 w-full text-center"
            placeholder="Email for magic link"
          />
          <Button onClick={handleMagicLinkLogin} className="w-full">Send Magic Link</Button>
        </div>
      )}
      {sent && <p className="text-green-600 text-center text-sm">Check your email!</p>}
      {errorMsg && <p className="text-red-600 text-center text-sm">{errorMsg}</p>}
    </div>
  );
}
