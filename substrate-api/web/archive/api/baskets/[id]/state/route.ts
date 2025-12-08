import { NextRequest, NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser'
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  if (process.env.MOCK_BASKET_API) {
    return NextResponse.json({ id, name: 'Mock Basket', status: 'INIT', last_activity_ts: new Date().toISOString() })
  }

  const supabase = createServerSupabaseClient()
  const { userId } = await getAuthenticatedUser(supabase)
  const ws = await ensureWorkspaceForUser(userId, supabase)

  const { data: basket, error: bErr } = await supabase
    .from('baskets')
    .select('id,name,status,created_at')
    .eq('id', id)
    .eq('workspace_id', ws.id)
    .maybeSingle()

  if (bErr) return NextResponse.json({ error: bErr.message }, { status: 400 })
  if (!basket) return NextResponse.json({ error: 'not_found' }, { status: 404 })

  const { data: events } = await supabase
    .from('timeline_events')
    .select('ts')
    .eq('basket_id', id)
    .order('ts', { ascending: false })
    .limit(1)

  const last_activity_ts = events?.[0]?.ts ?? basket.created_at
  return NextResponse.json({ id: basket.id, name: basket.name, status: basket.status, last_activity_ts })
}
