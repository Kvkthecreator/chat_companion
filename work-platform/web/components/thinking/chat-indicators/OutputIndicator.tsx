'use client';

/**
 * OutputIndicator
 *
 * Inline indicator showing work outputs ready for review.
 * Clicking opens the Outputs window with the outputs highlighted.
 *
 * Part of Desktop UI Architecture v1.0
 * See: /docs/implementation/DESKTOP_UI_IMPLEMENTATION_PLAN.md
 */

import { Lightbulb, ChevronRight, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TPWorkOutputPreview } from '@/lib/types/thinking-partner';

interface OutputIndicatorProps {
  /** Work outputs to display */
  outputs: TPWorkOutputPreview[];
  /** Callback when clicked - opens Outputs window */
  onOpen?: (outputIds: string[]) => void;
  /** Compact mode for inline display */
  compact?: boolean;
  className?: string;
}

export function OutputIndicator({
  outputs,
  onOpen,
  compact = false,
  className,
}: OutputIndicatorProps) {
  if (outputs.length === 0) return null;

  const outputIds = outputs.map((o) => o.id);

  // Count by status
  const pendingCount = outputs.filter(
    (o) => o.supervision_status === 'pending_review'
  ).length;
  const approvedCount = outputs.filter(
    (o) => o.supervision_status === 'approved'
  ).length;
  const rejectedCount = outputs.filter(
    (o) => o.supervision_status === 'rejected'
  ).length;

  // Get output types
  const outputTypes = [...new Set(outputs.map((o) => o.output_type))];
  const typesList = outputTypes.slice(0, 2).join(', ');

  const handleClick = () => {
    if (onOpen && outputIds.length > 0) {
      onOpen(outputIds);
    }
  };

  // Determine primary color based on pending status
  const hasPending = pendingCount > 0;
  const colorClasses = hasPending
    ? {
        border: 'border-amber-200',
        bg: 'bg-amber-50/50',
        bgHover: 'hover:bg-amber-100/50',
        text: 'text-amber-900',
        subtext: 'text-amber-700/70',
        iconBg: 'bg-amber-100',
        iconText: 'text-amber-600',
        chevron: 'text-amber-400',
      }
    : {
        border: 'border-green-200',
        bg: 'bg-green-50/50',
        bgHover: 'hover:bg-green-100/50',
        text: 'text-green-900',
        subtext: 'text-green-700/70',
        iconBg: 'bg-green-100',
        iconText: 'text-green-600',
        chevron: 'text-green-400',
      };

  if (compact) {
    return (
      <button
        onClick={handleClick}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs transition-colors',
          colorClasses.border,
          colorClasses.bg,
          colorClasses.bgHover,
          colorClasses.text,
          className
        )}
      >
        <Lightbulb className="h-3 w-3" />
        <span>
          {outputs.length} output{outputs.length > 1 ? 's' : ''}
        </span>
        {pendingCount > 0 && (
          <span className="flex items-center gap-0.5 text-amber-600">
            <Clock className="h-3 w-3" />
            {pendingCount}
          </span>
        )}
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      className={cn(
        'flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors',
        colorClasses.border,
        colorClasses.bg,
        colorClasses.bgHover,
        className
      )}
    >
      <div className={cn('rounded-md p-2', colorClasses.iconBg)}>
        <Lightbulb className={cn('h-4 w-4', colorClasses.iconText)} />
      </div>
      <div className="flex-1 min-w-0">
        <div className={cn('flex items-center gap-2 text-sm font-medium', colorClasses.text)}>
          Output Ready: {outputs.length} item{outputs.length > 1 ? 's' : ''}
        </div>
        <div className={cn('flex items-center gap-2 text-xs', colorClasses.subtext)}>
          {pendingCount > 0 && (
            <span className="flex items-center gap-1 text-amber-600">
              <Clock className="h-3 w-3" />
              {pendingCount} pending
            </span>
          )}
          {approvedCount > 0 && (
            <span className="flex items-center gap-1 text-green-600">
              <CheckCircle2 className="h-3 w-3" />
              {approvedCount} approved
            </span>
          )}
          {rejectedCount > 0 && (
            <span className="flex items-center gap-1 text-red-600">
              <XCircle className="h-3 w-3" />
              {rejectedCount} rejected
            </span>
          )}
          {outputTypes.length > 0 && (
            <span className="text-muted-foreground">
              ({typesList})
            </span>
          )}
        </div>
      </div>
      <ChevronRight className={cn('h-4 w-4 shrink-0', colorClasses.chevron)} />
    </button>
  );
}

export default OutputIndicator;
