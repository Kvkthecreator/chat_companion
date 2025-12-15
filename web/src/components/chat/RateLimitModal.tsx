"use client";

import { Clock, Crown, ShoppingCart } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useSubscription } from "@/hooks/useSubscription";

interface RateLimitModalProps {
  open: boolean;
  onClose: () => void;
  resetAt?: string;
  cooldownSeconds?: number;
}

export function RateLimitModal({
  open,
  onClose,
  resetAt,
  cooldownSeconds,
}: RateLimitModalProps) {
  const { isPremium, upgrade, isLoading } = useSubscription();

  // Format the reset time
  const formatResetTime = () => {
    if (cooldownSeconds && cooldownSeconds > 0) {
      const minutes = Math.ceil(cooldownSeconds / 60);
      if (minutes < 60) {
        return `${minutes} minute${minutes > 1 ? "s" : ""}`;
      }
      const hours = Math.ceil(minutes / 60);
      return `${hours} hour${hours > 1 ? "s" : ""}`;
    }
    if (resetAt) {
      const resetDate = new Date(resetAt);
      const now = new Date();
      const diffMs = resetDate.getTime() - now.getTime();
      const diffMins = Math.ceil(diffMs / 60000);
      if (diffMins < 60) {
        return `${diffMins} minute${diffMins > 1 ? "s" : ""}`;
      }
      const diffHours = Math.ceil(diffMins / 60);
      return `${diffHours} hour${diffHours > 1 ? "s" : ""}`;
    }
    return "a few minutes";
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-amber-500" />
            Slow Down a Little
          </DialogTitle>
          <DialogDescription>
            You&apos;re chatting faster than we can keep up! Take a short break
            and try again in {formatResetTime()}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-4">
          {!isPremium && (
            <div className="rounded-lg bg-purple-500/10 border border-purple-500/20 p-4">
              <p className="text-sm text-muted-foreground mb-3">
                Premium members enjoy much higher message limits and faster
                cooldowns.
              </p>
              <Button
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                onClick={() => {
                  upgrade();
                  onClose();
                }}
                disabled={isLoading}
              >
                <Crown className="h-4 w-4 mr-2" />
                Upgrade to Premium
              </Button>
            </div>
          )}

          <Button variant="ghost" className="w-full" onClick={onClose}>
            Got it, I&apos;ll wait
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
