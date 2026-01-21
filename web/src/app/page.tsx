import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { SectionHeader } from "@/components/ui/section-header";
import { RotatingHero } from "@/components/landing";

export default async function Home() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const isLoggedIn = !!user;

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b bg-background/80 backdrop-blur sticky top-0 z-50">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border/60 bg-muted/60 shadow-sm shrink-0">
              <span className="text-xl">💬</span>
            </div>
            <div>
              <h1 className="text-xl font-bold leading-tight text-foreground">
                Chat Companion
              </h1>
              <p className="text-xs text-muted-foreground">Your AI friend</p>
            </div>
          </Link>

          {/* Auth button */}
          {isLoggedIn ? (
            <Link
              href="/dashboard"
              className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition hover:bg-primary/90"
            >
              Continue
            </Link>
          ) : (
            <Link
              href="/login?next=/dashboard"
              className="rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition hover:bg-primary/90"
            >
              Sign in
            </Link>
          )}
        </div>
      </header>

      <main className="relative mx-auto flex max-w-6xl flex-col gap-16 px-6 py-12">
        {/* Hero with chat preview */}
        <RotatingHero />

        {/* How it works section */}
        <section className="relative overflow-hidden rounded-2xl border bg-card">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-purple-500/10 via-transparent to-transparent" />
          <div className="relative grid gap-6 p-6 sm:p-8 md:grid-cols-2 md:gap-8">
            {/* Left: Copy */}
            <div className="flex flex-col justify-center gap-4">
              <div className="flex items-center gap-2">
                <span className="rounded-full bg-purple-100 dark:bg-purple-900/50 px-3 py-1 text-xs font-medium text-purple-700 dark:text-purple-300">
                  How it works
                </span>
              </div>
              <h2 className="text-2xl font-bold text-foreground sm:text-3xl">
                Your companion reaches out to you
              </h2>
              <p className="text-foreground/70">
                Unlike other AI apps, your companion initiates conversations.
                Set your preferred times and channels, and your companion will check in on you.
              </p>
              <ul className="flex flex-col gap-2 text-sm text-foreground/70">
                <li className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 text-purple-500 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Daily check-ins at your preferred time
                </li>
                <li className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 text-purple-500 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Remembers your life and conversations
                </li>
                <li className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 text-purple-500 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  Telegram, WhatsApp, or Web - your choice
                </li>
              </ul>
              <div className="pt-2">
                <Link
                  href="/login?next=/onboarding"
                  className="inline-flex items-center gap-2 rounded-full bg-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-purple-700"
                >
                  Get started
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                </Link>
              </div>
            </div>

            {/* Right: Visual */}
            <div className="flex items-center justify-center">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="flex flex-col items-center gap-2 p-4">
                  <div className="h-12 w-12 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center text-2xl">
                    🌅
                  </div>
                  <span className="text-sm font-medium">Morning</span>
                </div>
                <div className="flex flex-col items-center gap-2 p-4">
                  <div className="h-12 w-12 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center text-2xl">
                    ☀️
                  </div>
                  <span className="text-sm font-medium">Afternoon</span>
                </div>
                <div className="flex flex-col items-center gap-2 p-4">
                  <div className="h-12 w-12 rounded-full bg-purple-100 dark:bg-purple-900/50 flex items-center justify-center text-2xl">
                    🌙
                  </div>
                  <span className="text-sm font-medium">Evening</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Social proof / Trust */}
        <section className="text-center space-y-2">
          <p className="text-sm text-muted-foreground">
            A companion that actually reaches out to you
          </p>
          <p className="text-xs text-muted-foreground/60">
            Free to start. No credit card required.
          </p>
        </section>

        {/* Privacy */}
        <section className="space-y-3 rounded-xl border bg-card p-6 shadow-sm">
          <SectionHeader title="Privacy & Safety" />
          <p className="text-sm text-muted-foreground">
            Sign-in required to chat. Your conversations stay private and are
            never used for training.
          </p>
        </section>
      </main>

      <footer className="border-t bg-background/80 backdrop-blur">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">💬</span>
              <span className="text-sm text-muted-foreground">Chat Companion</span>
            </div>
            <nav className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
              {!isLoggedIn && (
                <Link
                  href="/login?next=/dashboard"
                  className="hover:text-foreground"
                >
                  Sign in
                </Link>
              )}
              <Link href="/privacy" className="hover:text-foreground">
                Privacy Policy
              </Link>
              <Link href="/terms" className="hover:text-foreground">
                Terms of Service
              </Link>
            </nav>
          </div>
          <div className="mt-6 border-t pt-6 text-center text-xs text-muted-foreground">
            <p>&copy; {new Date().getFullYear()} Chat Companion. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
