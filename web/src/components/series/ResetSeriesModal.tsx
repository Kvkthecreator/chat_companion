"use client";

import { useState } from "react";
import { AlertTriangle, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";

interface ResetSeriesModalProps {
  open: boolean;
  onClose: () => void;
  seriesId: string;
  seriesTitle: string;
  onResetComplete?: () => void;
}

export function ResetSeriesModal({
  open,
  onClose,
  seriesId,
  seriesTitle,
  onResetComplete,
}: ResetSeriesModalProps) {
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleReset = async () => {
    if (!isConfirmed) return;

    setIsResetting(true);
    setError(null);

    try {
      await api.series.reset(seriesId);
      onResetComplete?.();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reset series progress");
    } finally {
      setIsResetting(false);
    }
  };

  const handleClose = () => {
    if (isResetting) return;
    setIsConfirmed(false);
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-destructive">
            <AlertTriangle className="h-5 w-5" />
            Reset Series Progress
          </DialogTitle>
          <DialogDescription>
            This will permanently erase your progress in {seriesTitle}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          <div className="rounded-lg bg-destructive/10 p-4 space-y-2">
            <p className="text-sm font-medium text-destructive">
              This action will delete:
            </p>
            <ul className="text-sm text-muted-foreground space-y-1 ml-4 list-disc">
              <li>All episode sessions and messages in this series</li>
              <li>All memories from this series</li>
              <li>Your episode completion status</li>
            </ul>
          </div>

          <label className="flex items-start gap-3 pt-2 cursor-pointer">
            <input
              type="checkbox"
              checked={isConfirmed}
              onChange={(e) => setIsConfirmed(e.target.checked)}
              disabled={isResetting}
              className="mt-0.5 h-4 w-4 rounded border-border text-primary focus:ring-primary focus:ring-offset-0 disabled:opacity-50"
            />
            <span className="text-sm text-muted-foreground leading-tight">
              I understand this action is permanent and cannot be undone
            </span>
          </label>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <div className="flex gap-3 pt-2">
            <Button
              variant="outline"
              className="flex-1"
              onClick={handleClose}
              disabled={isResetting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              className="flex-1"
              onClick={handleReset}
              disabled={!isConfirmed || isResetting}
            >
              {isResetting ? (
                "Resetting..."
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Reset Progress
                </>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
