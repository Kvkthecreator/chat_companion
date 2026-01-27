'use client'

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Home, MessageCircle, Settings, Brain } from "lucide-react"
import { cn } from "@/lib/utils"

const navItems = [
  { name: "Home", href: "/dashboard", icon: Home },
  { name: "Chat", href: "/chat", icon: MessageCircle },
  { name: "Memory", href: "/memory", icon: Brain },
  { name: "Settings", href: "/settings", icon: Settings },
]

export function MobileBottomNav() {
  const pathname = usePathname()

  // Don't show on onboarding or auth pages
  if (pathname.startsWith('/onboarding') || pathname.startsWith('/login') || pathname.startsWith('/auth')) {
    return null
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:hidden">
      <div className="flex h-16 items-center justify-around px-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href ||
            (item.href !== '/dashboard' && pathname.startsWith(item.href))

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex flex-col items-center justify-center gap-1 px-3 py-2 text-xs font-medium transition-colors",
                isActive
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <item.icon
                className={cn(
                  "h-5 w-5",
                  isActive ? "text-primary" : "text-muted-foreground"
                )}
              />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </div>
      {/* Safe area padding for iOS */}
      <div className="h-[env(safe-area-inset-bottom)]" />
    </nav>
  )
}
