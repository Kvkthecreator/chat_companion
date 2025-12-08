import { NextResponse } from 'next/server'
import { randomUUID } from 'crypto'
import { createServerSupabaseClient } from '@/lib/supabase/server'
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser'
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser'
import { getOrCreateDefaultBasket } from '@/lib/baskets/getOrCreateDefaultBasket'
import { log } from '@/lib/server/log'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET() {
  const supabase = createServerSupabaseClient()
  const { userId } = await getAuthenticatedUser(supabase)
  log('RESOLVE_API_GET_START', { userId })
  const ws = await ensureWorkspaceForUser(userId, supabase)

  const { data, error } = await supabase
    .from('baskets')
    .select('id,status,created_at')
    .eq('workspace_id', ws.id)
    .order('created_at', { ascending: false })
    .limit(1)

  if (error) {
    log('RESOLVE_API_GET_END', { userId, error: error.message })
    return NextResponse.json({ error: error.message }, { status: 400 })
  }
  if (!data || data.length === 0) {
    log('RESOLVE_API_GET_END', { userId, status: 404 })
    return NextResponse.json({ error: 'no_basket' }, { status: 404 })
  }
  log('RESOLVE_API_GET_END', { userId, basketId: data[0].id })
  return NextResponse.json({ id: data[0].id })
}

export async function POST(req: Request) {
  const supabase = createServerSupabaseClient()
  const { userId } = await getAuthenticatedUser(supabase)
  log('RESOLVE_API_POST_START', { userId })
  const ws = await ensureWorkspaceForUser(userId, supabase)
  try {
    const basket = await getOrCreateDefaultBasket({
      workspaceId: ws.id,
      idempotencyKey: randomUUID(),
      name: 'Default Basket',
    })
    log('RESOLVE_API_POST_END', { userId, basketId: basket.id })
    return NextResponse.json({ id: basket.id })
  } catch (e: any) {
    log('RESOLVE_API_POST_END', { userId, error: e.message })
    return NextResponse.json({ error: 'failed' }, { status: 500 })
  }
}
