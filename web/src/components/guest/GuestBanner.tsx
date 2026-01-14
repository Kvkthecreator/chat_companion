"use client";

import { Button } from "@/components/ui/button";

interface GuestBannerProps {
  messagesRemaining: number;
  onSignup: () => void;
}

export function GuestBanner({ messagesRemaining, onSignup }: GuestBannerProps) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm dark:border-amber-800 dark:bg-amber-950">
      <div className="flex items-center gap-2">
        <span className="font-medium text-amber-900 dark:text-amber-100">
          Trial mode
        </span>
        <span className="text-amber-700 dark:text-amber-300">•</span>
        <span className="text-amber-700 dark:text-amber-300">
          {messagesRemaining} {messagesRemaining === 1 ? "message" : "messages"} remaining
        </span>
      </div>
      <Button
        size="sm"
        variant="outline"
        onClick={onSignup}
        className="border-amber-300 bg-white hover:bg-amber-50 dark:border-amber-700 dark:bg-amber-900 dark:hover:bg-amber-800"
      >
        Sign up free
      </Button>
    </div>
  );
}
