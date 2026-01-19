'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { api } from '@/lib/api/client'
import type { AdminStatsResponse, AdminUserEngagement, AdminSignupDay, ActivationFunnelResponse } from '@/types'
import { Users, DollarSign, MessageSquare, Sparkles, TrendingUp, Download, Activity, UserX, Filter, AlertTriangle, CheckCircle, ArrowDown } from 'lucide-react'

function formatCurrency(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}

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

function exportToCSV(stats: AdminStatsResponse) {
  const { overview, users, signups_by_day } = stats

  // Build CSV content
  let csv = 'EP-0 Analytics Export\n'
  csv += `Generated: ${new Date().toISOString()}\n\n`

  // Overview
  csv += 'OVERVIEW\n'
  csv += `Total Users,${overview.total_users}\n`
  csv += `Users (7d),${overview.users_7d}\n`
  csv += `Users (30d),${overview.users_30d}\n`
  csv += `Premium Users,${overview.premium_users}\n`
  csv += `Conversion Rate,${overview.total_users > 0 ? ((overview.premium_users / overview.total_users) * 100).toFixed(1) : 0}%\n`
  csv += `Total Revenue,$${(overview.total_revenue_cents / 100).toFixed(2)}\n`
  csv += `Total Messages,${overview.total_messages}\n`
  csv += `Total Sessions,${overview.total_sessions}\n`
  csv += `Avg Messages/Session,${overview.total_sessions > 0 ? (overview.total_messages / overview.total_sessions).toFixed(1) : 0}\n\n`

  // Signups
  csv += 'DAILY SIGNUPS (Last 30 Days)\n'
  csv += 'Date,Count\n'
  signups_by_day.forEach(day => {
    csv += `${day.date},${day.count}\n`
  })
  csv += '\n'

  // Users
  csv += 'USERS\n'
  csv += 'Name,Status,Source,Campaign,Messages,Images,Sparks,Sessions,Signed Up\n'
  users.forEach(user => {
    csv += `"${user.display_name}",${user.subscription_status},"${user.signup_source || 'unknown'}","${user.signup_campaign || '-'}",${user.messages_sent_count},${user.flux_generations_used},${user.spark_balance},${user.session_count},${user.created_at}\n`
  })

  // Download
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ep0-analytics-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function SimpleBarChart({ data }: { data: AdminSignupDay[] }) {
  if (data.length === 0) {
    return <div className="text-muted-foreground text-sm">No signup data yet</div>
  }

  const maxCount = Math.max(...data.map(d => d.count), 1)
  const totalSignups = data.reduce((sum, d) => sum + d.count, 0)

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        {totalSignups} signups in the last 30 days
      </div>
      <div className="flex items-end gap-1 h-40 pb-8">
        {data.map((day, i) => (
          <div key={i} className="flex-1 flex flex-col items-center relative group">
            {/* Bar */}
            <div className="w-full flex-1 flex items-end">
              <div
                className="w-full bg-primary rounded-t min-h-[8px] transition-all hover:bg-primary/80"
                style={{ height: `${Math.max((day.count / maxCount) * 100, 5)}%` }}
              />
            </div>
            {/* Count on hover */}
            <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-foreground text-background px-1.5 py-0.5 rounded text-xs opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              {day.count}
            </div>
            {/* Date label */}
            <span className="absolute -bottom-6 text-[9px] text-muted-foreground -rotate-45 origin-top-left whitespace-nowrap">
              {formatDate(day.date)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// Funnel visualization component
function FunnelChart({ data }: { data: ActivationFunnelResponse['funnel'] }) {
  return (
    <div className="space-y-2">
      {data.map((step, i) => {
        const prevPercentage = i > 0 ? data[i - 1].percentage : 100
        const dropoff = prevPercentage - step.percentage
        const isSignificantDrop = dropoff > 15

        return (
          <div key={step.step} className="relative">
            <div className="flex items-center gap-3">
              <div className="w-32 text-sm text-right text-muted-foreground truncate" title={step.step}>
                {step.step}
              </div>
              <div className="flex-1 relative">
                <div className="h-8 bg-muted rounded overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      step.percentage > 50 ? 'bg-green-500' :
                      step.percentage > 25 ? 'bg-yellow-500' :
                      step.percentage > 10 ? 'bg-orange-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${step.percentage}%` }}
                  />
                </div>
              </div>
              <div className="w-20 text-sm tabular-nums">
                <span className="font-medium">{step.percentage}%</span>
                <span className="text-muted-foreground ml-1">({step.count})</span>
              </div>
              {i > 0 && isSignificantDrop && (
                <div className="w-16 text-xs text-red-500 flex items-center gap-1">
                  <ArrowDown className="h-3 w-3" />
                  -{dropoff.toFixed(0)}%
                </div>
              )}
              {i > 0 && !isSignificantDrop && <div className="w-16" />}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Message distribution bar chart
function MessageDistributionChart({ data }: { data: ActivationFunnelResponse['message_distribution'] }) {
  const maxPercentage = Math.max(...data.map(d => d.percentage), 1)

  return (
    <div className="space-y-2">
      {data.map((bucket) => (
        <div key={bucket.bucket} className="flex items-center gap-3">
          <div className="w-16 text-sm text-right text-muted-foreground">
            {bucket.bucket === '0' ? '0 msgs' : `${bucket.bucket}`}
          </div>
          <div className="flex-1 relative">
            <div className="h-6 bg-muted rounded overflow-hidden">
              <div
                className={`h-full ${bucket.bucket === '0' ? 'bg-red-500' : 'bg-primary'}`}
                style={{ width: `${(bucket.percentage / maxPercentage) * 100}%` }}
              />
            </div>
          </div>
          <div className="w-20 text-sm tabular-nums">
            <span className="font-medium">{bucket.percentage}%</span>
            <span className="text-muted-foreground ml-1">({bucket.count})</span>
          </div>
        </div>
      ))}
    </div>
  )
}

// Cohort retention table
function CohortRetentionTable({ data }: { data: ActivationFunnelResponse['cohort_retention'] }) {
  if (data.length === 0) {
    return <div className="text-muted-foreground text-sm">No cohort data yet</div>
  }

  const formatRetention = (val: number) => {
    if (val === 0) return <span className="text-muted-foreground">-</span>
    return (
      <span className={val > 20 ? 'text-green-500 font-medium' : val > 10 ? 'text-yellow-500' : 'text-red-500'}>
        {val.toFixed(0)}%
      </span>
    )
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b">
          <th className="text-left py-2 px-2 font-medium">Week</th>
          <th className="text-right py-2 px-2 font-medium">Users</th>
          <th className="text-right py-2 px-2 font-medium">D1</th>
          <th className="text-right py-2 px-2 font-medium">D7</th>
          <th className="text-right py-2 px-2 font-medium">D14</th>
          <th className="text-right py-2 px-2 font-medium">D30</th>
        </tr>
      </thead>
      <tbody>
        {data.map((cohort) => (
          <tr key={cohort.cohort_date} className="border-b border-border/50">
            <td className="py-2 px-2">{cohort.cohort_date}</td>
            <td className="text-right py-2 px-2 tabular-nums">{cohort.cohort_size}</td>
            <td className="text-right py-2 px-2 tabular-nums">{formatRetention(cohort.day_1)}</td>
            <td className="text-right py-2 px-2 tabular-nums">{formatRetention(cohort.day_7)}</td>
            <td className="text-right py-2 px-2 tabular-nums">{formatRetention(cohort.day_14)}</td>
            <td className="text-right py-2 px-2 tabular-nums">{formatRetention(cohort.day_30)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStatsResponse | null>(null)
  const [funnel, setFunnel] = useState<ActivationFunnelResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const [statsData, funnelData] = await Promise.all([
        api.admin.stats(),
        api.admin.funnel(30)
      ])
      setStats(statsData)
      setFunnel(funnelData)
    } catch (err) {
      console.error('Failed to fetch admin stats:', err)
      setError(err instanceof Error ? err.message : 'Failed to load stats')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Admin</p>
          <h1 className="mt-2 text-3xl font-semibold">Analytics Dashboard</h1>
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
      <div className="space-y-8">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Admin</p>
          <h1 className="mt-2 text-3xl font-semibold">Analytics Dashboard</h1>
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

  const { overview, signups_by_day, users, purchases, guest_sessions } = stats

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Admin</p>
          <h1 className="mt-2 text-3xl font-semibold">Analytics Dashboard</h1>
          <p className="mt-2 text-muted-foreground">
            Product metrics and user engagement
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => exportToCSV(stats)} className="gap-2">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.total_users}</div>
            <p className="text-xs text-muted-foreground">
              +{overview.users_7d} this week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Premium Users</CardTitle>
            <Sparkles className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.premium_users}</div>
            <p className="text-xs text-muted-foreground">
              {overview.total_users > 0
                ? `${((overview.premium_users / overview.total_users) * 100).toFixed(1)}% conversion`
                : '0% conversion'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(overview.total_revenue_cents)}</div>
            <p className="text-xs text-muted-foreground">
              From top-up purchases
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.total_messages.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {overview.total_sessions} sessions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Engagement</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {overview.total_sessions > 0
                ? (overview.total_messages / overview.total_sessions).toFixed(1)
                : '0'}
            </div>
            <p className="text-xs text-muted-foreground">
              avg msgs/session
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Guest Sessions</CardTitle>
            <UserX className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{overview.guest_sessions_total}</div>
            <p className="text-xs text-muted-foreground">
              +{overview.guest_sessions_24h} today, {overview.guest_sessions_converted} converted
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Signup Trends */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Signups (Last 30 Days)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <SimpleBarChart data={signups_by_day} />
        </CardContent>
      </Card>

      {/* Activation Funnel Section */}
      {funnel && (
        <>
          {/* Insights Alert */}
          {funnel.insights.length > 0 && (
            <Card className="border-yellow-500/50 bg-yellow-500/5">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-yellow-600">
                  <AlertTriangle className="h-4 w-4" />
                  Activation Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {funnel.insights.map((insight, i) => (
                    <li key={i} className="text-sm">{insight}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Funnel + Message Distribution side by side */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Filter className="h-4 w-4" />
                  Activation Funnel (30 days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <FunnelChart data={funnel.funnel} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Message Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <MessageDistributionChart data={funnel.message_distribution} />
              </CardContent>
            </Card>
          </div>

          {/* Dropoff Analysis + Source Performance */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ArrowDown className="h-4 w-4" />
                  Dropoff Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {funnel.dropoff_analysis.map((point, i) => (
                    <div key={i} className="flex items-start justify-between gap-4 pb-3 border-b border-border/50 last:border-0">
                      <div>
                        <div className="text-sm font-medium">{point.description}</div>
                        {point.example_users.length > 0 && (
                          <div className="text-xs text-muted-foreground mt-1">
                            e.g., {point.example_users.slice(0, 3).join(', ')}
                          </div>
                        )}
                      </div>
                      <div className="text-lg font-bold tabular-nums">{point.user_count}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" />
                  Source Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 font-medium">Source</th>
                        <th className="text-right py-2 font-medium">Signups</th>
                        <th className="text-right py-2 font-medium">Activation</th>
                        <th className="text-right py-2 font-medium">Engaged</th>
                      </tr>
                    </thead>
                    <tbody>
                      {funnel.source_performance.slice(0, 10).map((source, i) => (
                        <tr key={i} className="border-b border-border/50">
                          <td className="py-2">
                            <div className="font-medium">{source.source}</div>
                            {source.campaign && (
                              <div className="text-xs text-muted-foreground truncate max-w-[120px]" title={source.campaign}>
                                {source.campaign}
                              </div>
                            )}
                          </td>
                          <td className="text-right py-2 tabular-nums">{source.signups}</td>
                          <td className="text-right py-2 tabular-nums">
                            <span className={source.activation_rate > 50 ? 'text-green-500 font-medium' : source.activation_rate > 25 ? 'text-yellow-500' : 'text-muted-foreground'}>
                              {source.activation_rate}%
                            </span>
                          </td>
                          <td className="text-right py-2 tabular-nums">
                            <span className={source.engagement_rate > 30 ? 'text-green-500 font-medium' : 'text-muted-foreground'}>
                              {source.engagement_rate}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Cohort Retention */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Weekly Cohort Retention
              </CardTitle>
            </CardHeader>
            <CardContent>
              <CohortRetentionTable data={funnel.cohort_retention} />
            </CardContent>
          </Card>
        </>
      )}

      {/* Campaign Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Campaign Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2 font-medium">Source</th>
                  <th className="text-left py-2 px-2 font-medium">Campaign</th>
                  <th className="text-right py-2 px-2 font-medium">Signups</th>
                  <th className="text-right py-2 px-2 font-medium">Activated</th>
                  <th className="text-right py-2 px-2 font-medium">Activation %</th>
                </tr>
              </thead>
              <tbody>
                {(() => {
                  // Group users by source and campaign
                  const campaignStats = users.reduce((acc, user) => {
                    const key = `${user.signup_source || 'unknown'}|${user.signup_campaign || '-'}`;
                    if (!acc[key]) {
                      acc[key] = {
                        source: user.signup_source || 'unknown',
                        campaign: user.signup_campaign || '-',
                        total: 0,
                        activated: 0
                      };
                    }
                    acc[key].total += 1;
                    if (user.messages_sent_count > 0) {
                      acc[key].activated += 1;
                    }
                    return acc;
                  }, {} as Record<string, { source: string; campaign: string; total: number; activated: number }>);

                  return Object.values(campaignStats)
                    .sort((a, b) => b.total - a.total)
                    .map((stats, i) => (
                      <tr key={i} className="border-b border-border/50 hover:bg-muted/50">
                        <td className="py-2 px-2 font-medium">{stats.source}</td>
                        <td className="py-2 px-2 text-xs text-muted-foreground max-w-[200px] truncate" title={stats.campaign}>
                          {stats.campaign}
                        </td>
                        <td className="text-right py-2 px-2 tabular-nums">{stats.total}</td>
                        <td className="text-right py-2 px-2 tabular-nums">{stats.activated}</td>
                        <td className="text-right py-2 px-2 tabular-nums">
                          <span className={stats.activated > 0 ? 'text-green-500 font-medium' : 'text-muted-foreground'}>
                            {((stats.activated / stats.total) * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ));
                })()}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            User Engagement
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2 font-medium">User</th>
                  <th className="text-left py-2 px-2 font-medium">Status</th>
                  <th className="text-left py-2 px-2 font-medium">Source</th>
                  <th className="text-left py-2 px-2 font-medium">Campaign</th>
                  <th className="text-right py-2 px-2 font-medium">Messages</th>
                  <th className="text-right py-2 px-2 font-medium">Sessions</th>
                  <th className="text-left py-2 px-2 font-medium">Signed Up</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-border/50 hover:bg-muted/50">
                    <td className="py-2 px-2">
                      <div className="font-medium">{user.display_name}</div>
                    </td>
                    <td className="py-2 px-2">
                      <Badge variant={user.subscription_status === 'premium' ? 'default' : 'secondary'}>
                        {user.subscription_status}
                      </Badge>
                    </td>
                    <td className="py-2 px-2 text-xs text-muted-foreground">
                      {user.signup_source || 'unknown'}
                    </td>
                    <td className="py-2 px-2 text-xs text-muted-foreground max-w-[150px] truncate" title={user.signup_campaign || '-'}>
                      {user.signup_campaign || '-'}
                    </td>
                    <td className="text-right py-2 px-2 tabular-nums">
                      {user.messages_sent_count}
                    </td>
                    <td className="text-right py-2 px-2 tabular-nums">
                      {user.session_count}
                    </td>
                    <td className="py-2 px-2 text-muted-foreground">
                      {formatDate(user.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Recent Purchases */}
      {purchases.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Recent Purchases
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2 font-medium">User</th>
                    <th className="text-left py-2 px-2 font-medium">Pack</th>
                    <th className="text-right py-2 px-2 font-medium">Sparks</th>
                    <th className="text-right py-2 px-2 font-medium">Amount</th>
                    <th className="text-left py-2 px-2 font-medium">Status</th>
                    <th className="text-left py-2 px-2 font-medium">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {purchases.map((purchase) => (
                    <tr key={purchase.id} className="border-b border-border/50 hover:bg-muted/50">
                      <td className="py-2 px-2">{purchase.user_name}</td>
                      <td className="py-2 px-2 capitalize">{purchase.pack_name.replace('_', ' ')}</td>
                      <td className="text-right py-2 px-2 tabular-nums">{purchase.sparks_amount}</td>
                      <td className="text-right py-2 px-2 tabular-nums">{formatCurrency(purchase.price_cents)}</td>
                      <td className="py-2 px-2">
                        <Badge variant={purchase.status === 'completed' ? 'default' : 'secondary'}>
                          {purchase.status}
                        </Badge>
                      </td>
                      <td className="py-2 px-2 text-muted-foreground">
                        {formatDateTime(purchase.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Guest Sessions Table */}
      {guest_sessions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserX className="h-4 w-4" />
              Guest Sessions (Episode 0 Trials)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2 font-medium">Guest ID</th>
                    <th className="text-left py-2 px-2 font-medium">Character</th>
                    <th className="text-right py-2 px-2 font-medium">Messages</th>
                    <th className="text-left py-2 px-2 font-medium">IP Hash</th>
                    <th className="text-left py-2 px-2 font-medium">Status</th>
                    <th className="text-left py-2 px-2 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {guest_sessions.map((session) => (
                    <tr key={session.id} className="border-b border-border/50 hover:bg-muted/50">
                      <td className="py-2 px-2 font-mono text-xs">
                        {session.guest_session_id.slice(0, 8)}...
                      </td>
                      <td className="py-2 px-2">{session.character_name}</td>
                      <td className="text-right py-2 px-2 tabular-nums">{session.message_count}</td>
                      <td className="py-2 px-2 font-mono text-xs text-muted-foreground">
                        {session.ip_hash || '-'}
                      </td>
                      <td className="py-2 px-2">
                        {session.converted ? (
                          <Badge variant="default" className="bg-green-500">Converted</Badge>
                        ) : (
                          <Badge variant="secondary">Guest</Badge>
                        )}
                      </td>
                      <td className="py-2 px-2 text-muted-foreground">
                        {formatDateTime(session.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
