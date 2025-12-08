import { NextResponse } from 'next/server'
import { createServerSupabaseClient } from '@/lib/supabase/server'
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser'
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser'
import { listBasketsByWorkspace } from '@/lib/baskets/listBasketsByWorkspace'
import { pickMostRelevantBasket } from '@/lib/baskets/pickMostRelevantBasket'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export async function GET(req: Request) {
  const supabase = createServerSupabaseClient()
  const { userId } = await getAuthenticatedUser(supabase)
  const ws = await ensureWorkspaceForUser(userId, supabase)

  const { data: baskets } = await listBasketsByWorkspace(ws.id)
  if (!baskets?.length) {
    return NextResponse.redirect(new URL('/baskets', req.url))
  }
  const target = pickMostRelevantBasket({ baskets })!
  const res = NextResponse.redirect(new URL(`/baskets/${target.id}/overview`, req.url))

  // Cookie write is allowed here (Route Handler)
  res.cookies.set(`lastBasketId::${ws.id}`, target.id, {
    httpOnly: true, sameSite: 'lax', path: '/',
  })
  return res
}
