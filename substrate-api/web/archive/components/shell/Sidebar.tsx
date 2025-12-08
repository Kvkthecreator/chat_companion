"use client";

import { useEffect, useState, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, Inbox, Plug, LogOut, Settings2, FileText, Clock, Brain, Network, Layers, BookOpen, Shield, CloudUpload, ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { createBrowserClient } from "@/lib/supabase/clients";
import { getAllBaskets } from "@/lib/baskets/getAllBaskets";
import type { BasketOverview } from "@/lib/baskets/getAllBaskets";
import SidebarToggleIcon from "@/components/icons/SidebarToggleIcon";
import { useNavState } from "@/components/nav/useNavState";
import SidebarItem from "@/components/nav/SidebarItem";
import { SECTION_ORDER } from "@/components/features/baskets/sections";

interface SidebarProps {
  className?: string;
}

const supabase = createBrowserClient();

const GLOBAL_LINKS = [
  {
    href: '/dashboard',
    label: 'Control Tower',
    icon: LayoutDashboard,
  },
  {
    href: '/dashboard/integrations',
    label: 'Integrations',
    icon: Plug,
  },
  {
    href: '/workspace/change-requests',
    label: 'Change Requests',
    icon: Inbox,
  },
  {
    href: '/baskets',
    label: 'Context Baskets',
    icon: BookOpen,
  },
];

export default function Sidebar({ className }: SidebarProps) {
  const { open, setOpen, toggle } = useNavState();
  const pathname = usePathname();
  const router = useRouter();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [basket, setBasket] = useState<BasketOverview | null>(null);
  const [basketList, setBasketList] = useState<BasketOverview[]>([]);
  const [openDropdown, setOpenDropdown] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  // Mobile detection and responsive behavior
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      const wasMobile = isMobile;
      setIsMobile(mobile);

      // When switching from desktop to mobile, close sidebar to avoid covering content
      if (mobile && !wasMobile && open) {
        setOpen(false);
      }
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, [isMobile, open, setOpen]);

  useEffect(() => {
    async function init() {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser();
        setUserEmail(user?.email || null);

        const data = await getAllBaskets();
        setBasketList(data);

        const idFromPath = pathname?.match(/^\/baskets\/([^/]+)/)?.[1];
        if (idFromPath) {
          const fallback = data.find((item) => item.id === idFromPath);
          if (fallback) {
            setBasket(fallback);
          } else {
            setBasket({
              id: idFromPath,
              name: 'Untitled Basket',
              created_at: new Date().toISOString(),
              status: 'active',
            } as BasketOverview);
          }
        } else {
          setBasket(null);
        }
      } catch (err) {
        console.error("❌ Sidebar: Init error:", err);
        setBasket(null);
        setBasketList([]);
      }
    }
    init();
  }, [pathname]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (openDropdown && dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setOpenDropdown(false);
      }

      if (isMobile && open && !(e.target as HTMLElement).closest(".sidebar")) {
        setOpen(false);
      }
    }
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [openDropdown, isMobile, open, setOpen]);

  useEffect(() => {
    if (!isMobile) return;
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isMobile, open]);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/");
  };


  const handleNavigateToSettings = () => {
    try {
      router.push("/dashboard/settings");
      // Close sidebar on mobile after navigation
      if (isMobile) {
        setOpen(false);
      }
    } catch (error) {
      console.error("❌ Sidebar: Failed to navigate to settings:", error);
    }
  };

  const activeBasketId = pathname?.match(/^\/baskets\/([^/]+)/)?.[1] || null;
  const basketId = activeBasketId || basket?.id;
  const isBasketDetail = Boolean(activeBasketId);

  // Map section keys to icons
  const sectionIcons: Record<string, React.ElementType> = {
    memory: BookOpen,
    uploads: CloudUpload,
    governance: Shield,
    timeline: Clock,
    insights: Brain,
    graph: Network,
    "building-blocks": Layers,
    documents: FileText,
    settings: Settings2,
    "change-requests": Inbox,
  };

  return (
    <>
      {/* Scrim for mobile when sidebar is open */}
      {isMobile && (
        <div
          aria-hidden
          onClick={() => setOpen(false)}
          className={cn(
            "fixed inset-0 z-[49] bg-black/40 transition-opacity md:hidden",
            open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none",
          )}
        />
      )}

      <aside
        id="global-sidebar"
        className={cn(
          "sidebar h-screen w-64 border-r border-border transition-transform duration-300 flex flex-col z-[50]",
          isMobile ? "fixed top-0 left-0 bg-background/95 backdrop-blur-md shadow-xl" : "relative bg-card",
          open ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          !open && !isMobile && "hidden",
          className,
        )}
      >
        {/* Header */}
        <div
          className={cn(
            "sticky top-0 z-10 flex h-12 items-center justify-center border-b px-4",
            "bg-background/95 backdrop-blur-md",
          )}
        >
          <button
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              router.push("/");
            }}
            className="text-xl tracking-tight hover:underline font-brand"
          >
            yarnnn
          </button>
        </div>

        {/* Navigation */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {isBasketDetail && basket ? (
            <nav className="flex flex-1 flex-col gap-4 overflow-y-auto px-4 py-6">
              <button
                onClick={() => {
                  router.push('/dashboard');
                  if (isMobile) setOpen(false);
                }}
                className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft size={14} /> Back to Dashboard
              </button>
              <section className="space-y-2">
                <div className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Current Basket
                </div>
                <div className="rounded-md border-2 border-primary/40 bg-primary/5 px-3 py-2.5 text-sm font-semibold text-foreground shadow-sm">
                  {basket.name || 'Untitled Basket'}
                </div>
                <div className="flex flex-col gap-0.5 pt-2">
                  {SECTION_ORDER.filter((section) => section.key !== 'documents').map((section) => {
                    const href = section.href(basket.id);
                    const Icon = sectionIcons[section.key];
                    return (
                      <SidebarItem
                        key={section.key}
                        href={href}
                        onClick={() => {
                          if (isMobile) setOpen(false);
                        }}
                      >
                        <span className="flex items-center gap-2">
                          {Icon && <Icon size={14} />}
                          {section.label}
                        </span>
                      </SidebarItem>
                    );
                  })}
                  <SidebarItem
                    href={`/baskets/${basket.id}/documents`}
                    onClick={() => {
                      if (isMobile) setOpen(false);
                    }}
                  >
                    <span className="flex items-center gap-2">
                      <FileText size={14} /> Documents
                    </span>
                  </SidebarItem>
                </div>
              </section>
            </nav>
          ) : (
            <nav className="flex flex-1 flex-col gap-6 overflow-y-auto px-4 py-6">
              <section className="space-y-1">
                <p className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Dashboard
                </p>
                <div className="flex flex-col gap-0.5">
                  {GLOBAL_LINKS.map((item) => (
                    <SidebarItem
                      key={item.href}
                      href={item.href}
                      match="exact"
                      onClick={() => {
                        if (isMobile) setOpen(false);
                      }}
                    >
                      <span className="flex items-center gap-2">
                        <item.icon size={14} />
                        {item.label}
                      </span>
                    </SidebarItem>
                  ))}
                </div>
              </section>

              <section className="space-y-1">
                <p className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Context Baskets
                </p>
                <div className="flex flex-col gap-0.5">
                  {basketList.length === 0 ? (
                    <p className="px-3 py-2 text-sm text-muted-foreground">No context baskets yet</p>
                  ) : (
                    basketList.slice(0, 6).map((item) => (
                      <SidebarItem
                        key={item.id}
                        href={`/baskets/${item.id}/overview`}
                        match="startsWith"
                        onClick={() => {
                          if (isMobile) setOpen(false);
                        }}
                      >
                        {item.name || 'Untitled Basket'}
                      </SidebarItem>
                    ))
                  )}
                  {/* No "see all" button: global nav entry already routes via Context Baskets */}
                </div>
              </section>
            </nav>
          )}
        </div>

        {/* Footer + Dropdown */}
        <div className="relative border-t px-4 py-3">
          {userEmail ? (
            <div className="relative w-full" ref={dropdownRef}>
              <button
                onClick={() => setOpenDropdown(!openDropdown)}
                className="text-sm text-muted-foreground hover:text-foreground w-full text-left truncate"
              >
                {userEmail}
              </button>
              {openDropdown && (
                <div className="absolute bottom-12 left-0 w-52 rounded-md border bg-popover shadow-md z-50 py-1 text-sm">
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      setOpenDropdown(false);
                      handleNavigateToSettings();
                    }}
                    className="flex w-full items-center gap-2 px-4 py-2 hover:bg-muted text-muted-foreground hover:text-foreground"
                  >
                    <Settings2 size={14} />
                    Settings
                  </button>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      setOpenDropdown(false);
                      router.push("/governance/settings");
                      if (isMobile) setOpen(false);
                    }}
                    className="flex w-full items-center gap-2 px-4 py-2 hover:bg-muted text-muted-foreground hover:text-foreground"
                  >
                    <Shield size={14} />
                    Review Settings
                  </button>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      handleLogout();
                    }}
                    className="flex w-full items-center gap-2 px-4 py-2 text-destructive hover:bg-muted"
                  >
                    <LogOut size={14} />
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Not signed in</p>
          )}
        </div>
      </aside>
    </>
  );
}
