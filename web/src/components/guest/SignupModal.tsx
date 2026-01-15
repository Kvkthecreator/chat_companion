"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface SignupModalProps {
  open: boolean;
  onClose: () => void;
  guestSessionId: string | null;
  trigger: "message_limit" | "memory_snapshot";
}

export function SignupModal({
  open,
  onClose,
  guestSessionId,
  trigger,
}: SignupModalProps) {
  const handleSignup = () => {
    // Guest session ID stays in localStorage - GuestSessionConverter handles conversion after login
    // Redirect to login with return URL so user comes back to the chat page
    window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {trigger === "message_limit"
              ? "You've reached the trial limit"
              : "Sign up to continue"}
          </DialogTitle>
          <DialogDescription>
            {trigger === "message_limit"
              ? "Create an account to continue your conversation and unlock all episodes."
              : "The character remembers what you said. Sign up to see how this affects the story."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2 text-sm">
            <div className="flex items-start gap-2">
              <div className="mt-0.5 text-green-500">✓</div>
              <div>Unlimited messages in all episodes</div>
            </div>
            <div className="flex items-start gap-2">
              <div className="mt-0.5 text-green-500">✓</div>
              <div>Your choices are remembered across episodes</div>
            </div>
            <div className="flex items-start gap-2">
              <div className="mt-0.5 text-green-500">✓</div>
              <div>Continue through all episodes in every series</div>
            </div>
            <div className="flex items-start gap-2">
              <div className="mt-0.5 text-green-500">✓</div>
              <div>Try different story paths and endings</div>
            </div>
          </div>
        </div>

        <DialogFooter className="flex-col gap-2 sm:flex-col">
          <Button onClick={handleSignup} className="w-full">
            Continue with Google
          </Button>
          <Button variant="ghost" onClick={onClose} className="w-full">
            Not now
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
