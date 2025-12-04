"use client";

/**
 * WorkReviewClient - Client component for work output supervision
 *
 * Simplified to focus on quality review only:
 * - Approve: Mark output as usable
 * - Reject: Discard output with reason
 */

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  CheckCircle,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  FileText,
  Lightbulb,
  Target,
  BookOpen,
  MessageSquare,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/AlertDialog";
import { Textarea } from "@/components/ui/Textarea";
import { apiClient, ApiError } from "@/lib/api/http";

interface WorkOutput {
  id: string;
  output_type: string;
  agent_type: string;
  title: string;
  body: any;
  confidence: number;
  supervision_status: string;
  created_at: string;
  reviewed_at?: string;
  reviewer_notes?: string;
  work_tickets?: {
    id: string;
    status: string;
    metadata: any;
  };
}

interface Props {
  initialOutputs: WorkOutput[];
  basketId: string;
  projectId: string;
}

const OUTPUT_TYPE_ICONS: Record<string, React.ReactNode> = {
  finding: <Target className="h-4 w-4" />,
  recommendation: <Lightbulb className="h-4 w-4" />,
  insight: <BookOpen className="h-4 w-4" />,
  report_section: <FileText className="h-4 w-4" />,
  social_post: <MessageSquare className="h-4 w-4" />,
};

const STATUS_BADGES: Record<string, { variant: "default" | "success" | "destructive" | "warning" | "secondary"; label: string }> = {
  pending_review: { variant: "warning", label: "Pending Review" },
  approved: { variant: "success", label: "Approved" },
  rejected: { variant: "destructive", label: "Rejected" },
};

export function WorkReviewClient({
  initialOutputs,
  basketId,
  projectId,
}: Props) {
  const router = useRouter();
  const [outputs, setOutputs] = useState<WorkOutput[]>(initialOutputs);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Reject dialog state
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectOutputId, setRejectOutputId] = useState<string | null>(null);
  const [rejectNotes, setRejectNotes] = useState("");

  const handleApprove = useCallback(
    async (outputId: string) => {
      setActionLoading(outputId);

      try {
        const baseUrl = process.env.NEXT_PUBLIC_WORK_PLATFORM_API_URL || "";
        await apiClient({
          url: `${baseUrl}/api/supervision/baskets/${basketId}/outputs/${outputId}/approve`,
          method: "POST",
          body: { notes: null },
        });

        router.refresh();
      } catch (error) {
        console.error("[WorkReview] Approve failed:", error);
        const message = error instanceof ApiError ? error.message : (error instanceof Error ? error.message : "Unknown error");
        alert(`Failed to approve: ${message}`);
      } finally {
        setActionLoading(null);
      }
    },
    [basketId, router]
  );

  const handleRejectClick = (outputId: string) => {
    setRejectOutputId(outputId);
    setRejectNotes("");
    setRejectDialogOpen(true);
  };

  const handleRejectConfirm = useCallback(async () => {
    if (!rejectOutputId) return;

    setActionLoading(rejectOutputId);
    setRejectDialogOpen(false);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_WORK_PLATFORM_API_URL || "";
      await apiClient({
        url: `${baseUrl}/api/supervision/baskets/${basketId}/outputs/${rejectOutputId}/reject`,
        method: "POST",
        body: { notes: rejectNotes },
      });

      router.refresh();
    } catch (error) {
      console.error("[WorkReview] Reject failed:", error);
      const message = error instanceof ApiError ? error.message : (error instanceof Error ? error.message : "Unknown error");
      alert(`Failed to reject: ${message}`);
    } finally {
      setActionLoading(null);
      setRejectOutputId(null);
      setRejectNotes("");
    }
  }, [basketId, rejectOutputId, rejectNotes, router]);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-4">
      {outputs.length === 0 && (
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">No outputs to review</p>
        </Card>
      )}

      {outputs.map((output) => {
        const isExpanded = expandedId === output.id;
        const statusBadge = STATUS_BADGES[output.supervision_status] || STATUS_BADGES.pending_review;
        const isPendingReview = output.supervision_status === "pending_review";

        return (
          <Card key={output.id} className="overflow-hidden">
            {/* Header Row */}
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50"
              onClick={() => toggleExpand(output.id)}
            >
              <div className="flex items-center gap-3">
                <span className="text-muted-foreground">
                  {OUTPUT_TYPE_ICONS[output.output_type] || <FileText className="h-4 w-4" />}
                </span>
                <div>
                  <h3 className="font-medium text-foreground">{output.title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-muted-foreground capitalize">
                      {output.output_type.replace("_", " ")}
                    </span>
                    <span className="text-xs text-muted-foreground">•</span>
                    <span className="text-xs text-muted-foreground capitalize">
                      {output.agent_type} agent
                    </span>
                    <span className="text-xs text-muted-foreground">•</span>
                    <span className="text-xs text-muted-foreground">
                      {Math.round(output.confidence * 100)}% confidence
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge variant={statusBadge.variant}>{statusBadge.label}</Badge>
                {isExpanded ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </div>

            {/* Expanded Content */}
            {isExpanded && (
              <div className="border-t p-4 space-y-4">
                {/* Body Preview */}
                <div className="bg-muted/30 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">Content</h4>
                  <div className="text-sm text-foreground whitespace-pre-wrap">
                    {typeof output.body === "string"
                      ? output.body
                      : output.body?.summary || output.body?.content || JSON.stringify(output.body, null, 2)}
                  </div>
                </div>

                {/* Reviewer Notes (if rejected) */}
                {output.reviewer_notes && output.supervision_status === "rejected" && (
                  <div className="bg-destructive/10 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-destructive mb-2">Rejection Reason</h4>
                    <p className="text-sm text-foreground">{output.reviewer_notes}</p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between pt-2">
                  <div className="text-xs text-muted-foreground">
                    Created {new Date(output.created_at).toLocaleDateString()}
                    {output.reviewed_at && (
                      <> • Reviewed {new Date(output.reviewed_at).toLocaleDateString()}</>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {isPendingReview && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-destructive border-destructive hover:bg-destructive/10"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRejectClick(output.id);
                          }}
                          disabled={!!actionLoading}
                        >
                          <XCircle className="h-4 w-4 mr-1" />
                          Reject
                        </Button>
                        <Button
                          size="sm"
                          className="bg-success text-success-foreground hover:bg-success/90"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleApprove(output.id);
                          }}
                          disabled={!!actionLoading}
                        >
                          {actionLoading === output.id ? (
                            <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                          ) : (
                            <CheckCircle className="h-4 w-4 mr-1" />
                          )}
                          Approve
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </Card>
        );
      })}

      {/* Reject Dialog */}
      <AlertDialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Reject Output</AlertDialogTitle>
            <AlertDialogDescription>
              Please provide a reason for rejecting this output. This helps improve future agent work.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Textarea
            placeholder="Reason for rejection..."
            value={rejectNotes}
            onChange={(e) => setRejectNotes(e.target.value)}
            className="min-h-[100px]"
          />
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleRejectConfirm}
              disabled={!rejectNotes.trim()}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Reject
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
