import { createClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'
import { Sidebar } from '@/components/Sidebar'
import { MobileBottomNav } from '@/components/MobileBottomNav'

export const dynamic = 'force-dynamic'

export default async function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Check if user has completed onboarding
  const { data: userData } = await supabase
    .from('users')
    .select('onboarding_completed_at')
    .eq('id', user.id)
    .single()

  if (!userData?.onboarding_completed_at) {
    redirect('/onboarding')
  }

  return (
    <>
      <div className="flex h-[100dvh] bg-background text-foreground">
        {/* Sidebar - hidden on mobile, visible on md+ */}
        <div className="hidden md:block">
          <Sidebar user={user} variant="immersive" />
        </div>
        {/* Main content - full height */}
        <main className="flex-1 min-w-0 h-full overflow-hidden">
          {children}
        </main>
      </div>
      {/* Mobile bottom nav - only visible on mobile */}
      <MobileBottomNav />
    </>
  )
}
