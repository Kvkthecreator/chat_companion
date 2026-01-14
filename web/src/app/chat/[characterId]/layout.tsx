import { createClient } from '@/lib/supabase/server'
import { Sidebar } from '@/components/Sidebar'
import { ImmersiveLayoutWrapper } from '@/components/ImmersiveLayoutWrapper'
import { AttributionSaver } from '@/components/AttributionSaver'

export const dynamic = 'force-dynamic'

export default async function ChatLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  // Allow access for both authenticated and guest users
  // Guest users won't have a sidebar
  const sidebar = user ? <Sidebar user={user} /> : null

  return (
    <ImmersiveLayoutWrapper sidebar={sidebar}>
      <AttributionSaver />
      {children}
    </ImmersiveLayoutWrapper>
  )
}
