import { Suspense } from "react";
import LoginClient from "./LoginClient";
import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="min-h-screen w-full flex flex-col justify-center items-center px-4">
      <div className="w-full max-w-sm bg-card border rounded-xl shadow-sm px-6 py-8 space-y-6">
        {/* Header */}
        <div className="flex flex-col items-center space-y-1.5">
          <h2 className="text-2xl font-semibold tracking-tight">Sign in</h2>
          <p className="text-sm text-muted-foreground text-center">
            Continue to <span className="font-medium">yarnnn</span>
          </p>
        </div>

        {/* Login button */}
        <Suspense
          fallback={
            <div className="text-center text-sm text-muted-foreground">
              Loading login options...
            </div>
          }
        >
          <LoginClient />
        </Suspense>

        {/* Footer links */}
        <p className="text-xs text-center text-muted-foreground leading-relaxed">
          By continuing, you agree to our{" "}
          <Link
            href="/terms"
            className="underline underline-offset-2 hover:text-primary transition-colors"
          >
            Terms
          </Link>{" "}
          and{" "}
          <Link
            href="/privacy"
            className="underline underline-offset-2 hover:text-primary transition-colors"
          >
            Privacy Policy
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
