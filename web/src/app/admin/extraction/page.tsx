'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { api } from '@/lib/api/client'
import type { ExtractionStatsResponse } from '@/types'
import { ArrowLeft, AlertTriangle, CheckCircle, Clock, Database, TrendingDown, RefreshCw } from 'lucide-react'

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
}

function StatusBadge({ rate }: { rate: number }) {
  if (rate > 10) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-700">
        <AlertTriangle className="h-3 w-3" />
        Critical
      </span>
    )
  }
  if (rate > 5) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-700">
        <AlertTriangle className="h-3 w-3" />
        Warning
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-700">
      <CheckCircle className="h-3 w-3" />
      Healthy
    </span>
  )
}

function DailyChart({ data }: { data: ExtractionStatsResponse['daily_stats'] }) {
  if (data.length === 0) {
    return <div className="text-muted-foreground text-sm">No extraction data yet</div>
  }

  const maxTotal = Math.max(...data.map(d => d.total), 1)

  return (
    <div className="space-y-2">
      {data.map((day) => (
        <div key={day.date} className="flex items-center gap-3">
          <div className="w-20 text-sm text-muted-foreground">
            {formatDate(day.date)}
          </div>
          <div className="flex-1 relative h-6">
            <div className="absolute inset-0 bg-muted rounded" />
            <div
              className="absolute inset-y-0 left-0 bg-green-500 rounded-l"
              style={{ width: `${(day.success / maxTotal) * 100}%` }}
            />
            <div
              className="absolute inset-y-0 bg-red-500 rounded-r"
              style={{
                left: `${(day.success / maxTotal) * 100}%`,
                width: `${(day.failed / maxTotal) * 100}%`
              }}
            />
          </div>
          <div className="w-32 text-sm tabular-nums text-right">
            <span className="text-green-600">{day.success}</span>
            {' / '}
            <span className="text-red-600">{day.failed}</span>
            <span className="text-muted-foreground ml-2">
              ({day.failure_rate}%)
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function ExtractionPage() {
  const [stats, setStats] = useState<ExtractionStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.admin.extractionStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to fetch extraction stats:', err)
      setError(err instanceof Error ? err.message : 'Failed to load stats')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-8 p-8">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map(i => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-8 p-8">
        <div className="flex items-center gap-4">
          <Link href="/admin">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">Extraction Observability</h1>
            <p className="text-muted-foreground">Memory and thread extraction health</p>
          </div>
        </div>
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-destructive">{error}</p>
            <button
              onClick={fetchStats}
              className="mt-4 text-sm text-primary hover:underline"
            >
              Try again
            </button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="space-y-8 p-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/admin">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-semibold">Extraction Observability</h1>
            <p className="text-muted-foreground">Memory and thread extraction health</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={fetchStats} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Insights */}
      {stats.insights.length > 0 && (
        <Card className={
          stats.failure_rate_7d > 10 ? 'border-red-500/50 bg-red-500/5' :
          stats.failure_rate_7d > 5 ? 'border-yellow-500/50 bg-yellow-500/5' :
          'border-green-500/50 bg-green-500/5'
        }>
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              {stats.failure_rate_7d > 5 ? (
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-600" />
              )}
              System Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1">
              {stats.insights.map((insight, i) => (
                <li key={i} className="text-sm">{insight}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">24h Failure Rate</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{stats.failure_rate_24h}%</span>
              <StatusBadge rate={stats.failure_rate_24h} />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.failed_24h} of {stats.total_24h} extractions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">7d Failure Rate</CardTitle>
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{stats.failure_rate_7d}%</span>
              <StatusBadge rate={stats.failure_rate_7d} />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.failed_7d} of {stats.total_7d} extractions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.avg_duration_ms}ms</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.avg_duration_ms > 5000 ? 'Slow - check LLM latency' : 'Within normal range'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total (7d)</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_7d}</div>
            <p className="text-xs text-muted-foreground mt-1">
              extractions logged
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Daily Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            Daily Breakdown (Last 7 Days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <DailyChart data={stats.daily_stats} />
          <div className="flex items-center gap-4 mt-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-green-500" />
              Success
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded bg-red-500" />
              Failed
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Failures */}
      {stats.recent_failures.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              Recent Failures
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2 font-medium">Time</th>
                    <th className="text-left py-2 px-2 font-medium">Type</th>
                    <th className="text-left py-2 px-2 font-medium">User</th>
                    <th className="text-left py-2 px-2 font-medium">Error</th>
                    <th className="text-right py-2 px-2 font-medium">Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.recent_failures.map((failure, i) => (
                    <tr key={i} className="border-b border-border/50 hover:bg-muted/50">
                      <td className="py-2 px-2 text-muted-foreground">
                        {formatDateTime(failure.created_at)}
                      </td>
                      <td className="py-2 px-2">
                        <span className={`inline-flex px-2 py-0.5 text-xs rounded ${
                          failure.extraction_type === 'context'
                            ? 'bg-blue-100 text-blue-700'
                            : 'bg-purple-100 text-purple-700'
                        }`}>
                          {failure.extraction_type}
                        </span>
                      </td>
                      <td className="py-2 px-2">
                        {failure.user_display_name || '-'}
                      </td>
                      <td className="py-2 px-2 text-red-600 max-w-xs truncate" title={failure.error_message || ''}>
                        {failure.error_message || 'Unknown error'}
                      </td>
                      <td className="text-right py-2 px-2 tabular-nums text-muted-foreground">
                        {failure.duration_ms ? `${failure.duration_ms}ms` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Data State */}
      {stats.total_7d === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-lg font-medium">No extraction data yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Extraction logs will appear here after users send messages.
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Make sure the <code className="bg-muted px-1 rounded">extraction_logs</code> table migration has been applied.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
