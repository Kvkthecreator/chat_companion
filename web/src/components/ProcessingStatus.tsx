'use client'

import { cn } from '@/lib/utils'

interface ProcessingStatusProps {
  status: string
  size?: 'sm' | 'md'
  showLabel?: boolean
}

export function ProcessingStatus({ status, size = 'sm', showLabel = true }: ProcessingStatusProps) {
  const statusConfig: Record<string, { color: string; bgColor: string; label: string; animate?: boolean }> = {
    pending: { color: 'text-slate-600', bgColor: 'bg-slate-100', label: 'Pending' },
    processing: { color: 'text-blue-600', bgColor: 'bg-blue-100', label: 'Processing', animate: true },
    ready: { color: 'text-green-600', bgColor: 'bg-green-100', label: 'Ready' },
    failed: { color: 'text-red-600', bgColor: 'bg-red-100', label: 'Failed' },
    skipped: { color: 'text-slate-500', bgColor: 'bg-slate-50', label: 'Skipped' },
    uploaded: { color: 'text-amber-600', bgColor: 'bg-amber-100', label: 'Uploaded' },
  }

  const config = statusConfig[status] || statusConfig.pending
  const sizeClasses = size === 'sm' ? 'h-2 w-2' : 'h-3 w-3'
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm'

  return (
    <span className={cn('inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full', config.bgColor)}>
      <span className={cn(
        'rounded-full',
        sizeClasses,
        config.animate ? 'animate-pulse' : '',
        config.color.replace('text-', 'bg-')
      )} />
      {showLabel && (
        <span className={cn(textSize, 'font-medium', config.color)}>
          {config.label}
        </span>
      )}
    </span>
  )
}

export function EmbeddingStatusBadge({ status }: { status: string }) {
  return <ProcessingStatus status={status} size="sm" />
}
