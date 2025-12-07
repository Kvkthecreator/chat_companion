'use client';

/**
 * ContextIndicator
 *
 * Inline indicator showing context items used in a message.
 * Clicking opens the Context window with highlighted items.
 *
 * Part of Desktop UI Architecture v1.0
 * See: /docs/implementation/DESKTOP_UI_IMPLEMENTATION_PLAN.md
 */

import { FileText, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { TPContextChangeRich } from '@/lib/types/thinking-partner';

interface ContextIndicatorProps {
  /** Context items referenced in the message */
  items: TPContextChangeRich[];
  /** Callback when clicked - opens Context window */
  onOpen?: (itemIds: string[]) => void;
  /** Compact mode for inline display */
  compact?: boolean;
  className?: string;
}

export function ContextIndicator({
  items,
  onOpen,
  compact = false,
  className,
}: ContextIndicatorProps) {
  if (items.length === 0) return null;

  const itemIds = items
    .filter((i) => i.item_id)
    .map((i) => i.item_id as string);

  // Get unique item types
  const itemTypes = [...new Set(items.map((i) => i.item_type.replace('_', ' ')))];
  const typesList = itemTypes.slice(0, 3).join(', ');
  const hasMore = itemTypes.length > 3;

  const handleClick = () => {
    if (onOpen && itemIds.length > 0) {
      onOpen(itemIds);
    }
  };

  if (compact) {
    return (
      <button
        onClick={handleClick}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-xs text-blue-700 transition-colors hover:bg-blue-100',
          className
        )}
      >
        <FileText className="h-3 w-3" />
        <span>{items.length} context</span>
      </button>
    );
  }

  return (
    <button
      onClick={handleClick}
      className={cn(
        'flex w-full items-center gap-3 rounded-lg border border-blue-200 bg-blue-50/50 p-3 text-left transition-colors hover:bg-blue-100/50',
        className
      )}
    >
      <div className="rounded-md bg-blue-100 p-2">
        <FileText className="h-4 w-4 text-blue-600" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-sm font-medium text-blue-900">
          Context: {items.length} item{items.length > 1 ? 's' : ''} attached
        </div>
        <div className="text-xs text-blue-700/70 truncate">
          {typesList}
          {hasMore && ` +${itemTypes.length - 3} more`}
        </div>
      </div>
      <ChevronRight className="h-4 w-4 text-blue-400 shrink-0" />
    </button>
  );
}

export default ContextIndicator;
