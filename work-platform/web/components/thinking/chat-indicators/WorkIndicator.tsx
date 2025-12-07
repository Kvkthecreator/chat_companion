'use client';

/**
 * WorkIndicator
 *
 * Inline indicator showing work started or in progress.
 * Clicking opens the Work window with the ticket highlighted.
 *
 * Part of Desktop UI Architecture v1.0
 * See: /docs/implementation/DESKTOP_UI_IMPLEMENTATION_PLAN.md
 */

import { Zap, ChevronRight, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TPRecipeExecution } from '@/lib/types/thinking-partner';

interface WorkIndicatorProps {
  /** Recipe execution info */
  execution: TPRecipeExecution;
  /** Callback when clicked - opens Work window */
  onOpen?: (ticketId: string) => void;
  /** Compact mode for inline display */
  compact?: boolean;
  className?: string;
}

const STATUS_CONFIG = {
  queued: { icon: Zap, color: 'amber', label: 'Queued' },
  running: { icon: Loader2, color: 'blue', label: 'Running', animate: true },
  completed: { icon: CheckCircle2, color: 'green', label: 'Completed' },
  failed: { icon: XCircle, color: 'red', label: 'Failed' },
  cancelled: { icon: XCircle, color: 'gray', label: 'Cancelled' },
};

export function WorkIndicator({
  execution,
  onOpen,
  compact = false,
  className,
}: WorkIndicatorProps) {
  const config = STATUS_CONFIG[execution.status] || STATUS_CONFIG.queued;
  const Icon = config.icon;
  const isRunning = execution.status === 'running';

  const handleClick = () => {
    if (onOpen && execution.ticket_id) {
      onOpen(execution.ticket_id);
    }
  };

  // Color classes based on status
  const colorClasses = {
    amber: {
      border: 'border-amber-200',
      bg: 'bg-amber-50',
      bgHover: 'hover:bg-amber-100',
      text: 'text-amber-700',
      iconBg: 'bg-amber-100',
      iconText: 'text-amber-600',
    },
    blue: {
      border: 'border-blue-200',
      bg: 'bg-blue-50',
      bgHover: 'hover:bg-blue-100',
      text: 'text-blue-700',
      iconBg: 'bg-blue-100',
      iconText: 'text-blue-600',
    },
    green: {
      border: 'border-green-200',
      bg: 'bg-green-50',
      bgHover: 'hover:bg-green-100',
      text: 'text-green-700',
      iconBg: 'bg-green-100',
      iconText: 'text-green-600',
    },
    red: {
      border: 'border-red-200',
      bg: 'bg-red-50',
      bgHover: 'hover:bg-red-100',
      text: 'text-red-700',
      iconBg: 'bg-red-100',
      iconText: 'text-red-600',
    },
    gray: {
      border: 'border-gray-200',
      bg: 'bg-gray-50',
      bgHover: 'hover:bg-gray-100',
      text: 'text-gray-700',
      iconBg: 'bg-gray-100',
      iconText: 'text-gray-600',
    },
  };

  const colors = colorClasses[config.color as keyof typeof colorClasses];

  if (compact) {
    return (
      <button
        onClick={handleClick}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs transition-colors',
          colors.border,
          colors.bg,
          colors.bgHover,
          colors.text,
          className
        )}
      >
        <Icon className={cn('h-3 w-3', isRunning && 'animate-spin')} />
        <span>{config.label}</span>
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      className={cn(
        'flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors',
        colors.border,
        colors.bg,
        colors.bgHover,
        className
      )}
    >
      <div className={cn('rounded-md p-2', colors.iconBg)}>
        <Icon
          className={cn('h-4 w-4', colors.iconText, isRunning && 'animate-spin')}
        />
      </div>
      <div className="flex-1 min-w-0">
        <div className={cn('flex items-center gap-2 text-sm font-medium', colors.text)}>
          Work {config.label}: {execution.recipe_name || execution.recipe_slug}
        </div>
        <div className={cn('text-xs', colors.text, 'opacity-70')}>
          {execution.current_step || `Recipe: ${execution.recipe_slug}`}
          {isRunning && execution.progress_pct !== undefined && (
            <span className="ml-2">{execution.progress_pct}%</span>
          )}
        </div>
      </div>
      <ChevronRight className={cn('h-4 w-4 shrink-0', colors.text, 'opacity-50')} />
    </button>
  );
}

export default WorkIndicator;
