/**
 * Canon v1.3.1 Basket Dashboard
 * Task D: Basket Dashboard v1 (Canon Work Surface)
 */
import { Suspense } from 'react';
import { notFound, redirect } from 'next/navigation';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { DashboardQueries } from '@/lib/server/dashboard/queries';
import { BasketHeader } from '@/components/dashboard/BasketHeader';
import { ReflectionCard } from '@/components/dashboard/ReflectionCard';
import { RecentActivityCard } from '@/components/dashboard/RecentActivityCard';

interface PageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}

// Feature flag for Canon v1.3.1 dashboard
const CANON_DASHBOARD_ENABLED = process.env.CANON_DASHBOARD_ENABLED === 'true' || 
                                process.env.NODE_ENV === 'development';

export default async function DashboardPage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const searchParamsObj = await searchParams;

  // Feature flag check
  if (!CANON_DASHBOARD_ENABLED) {
    redirect(`/baskets/${id}/overview`);
  }

  // Authentication and workspace validation
  const supabase = createServerSupabaseClient();
  const { userId } = await getAuthenticatedUser(supabase);
  const workspace = await ensureWorkspaceForUser(userId, supabase);

  // Validate basket belongs to workspace
  const { data: basket, error: basketError } = await supabase
    .from('baskets')
    .select('id, name, workspace_id, created_at')
    .eq('id', id)
    .eq('workspace_id', workspace.id)
    .maybeSingle();

  if (basketError || !basket) {
    notFound();
  }

  // Load dashboard data
  const dashboardQueries = new DashboardQueries();
  
  const [health, recentDumps, recentReflection, timelineEvents] = await Promise.all([
    dashboardQueries.getBasketHealth(id),
    dashboardQueries.getRecentDumps(id, 3),
    dashboardQueries.getMostRecentReflection(id),
    dashboardQueries.getRecentTimelineEvents(id, 5),
  ]);

  // Fetch maintenance suggestions count (for badge)
  let suggestionsCount = 0;
  try {
    const res = await fetch(`/api/maintenance/suggest/${id}`, { cache: 'no-store' });
    if (res.ok) {
      const json = await res.json();
      const c = json?.candidates || {};
      const blocks = Array.isArray(c.blocks_to_archive) ? c.blocks_to_archive.length : 0;
      const dumps = Array.isArray(c.dumps_to_redact) ? c.dumps_to_redact.length : 0;
      const items = Array.isArray(c.context_items_to_deprecate) ? c.context_items_to_deprecate.length : 0;
      suggestionsCount = blocks + dumps + items;
    }
  } catch (_) {
    // Non-fatal: badge just won't show
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-6 space-y-6 max-w-4xl px-4">
        
        {/* Feature Flag Notice (development only) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <div className="text-sm text-blue-800">
              🧪 <strong>Canon v1.3.1 Dashboard</strong> - Feature flag active
            </div>
          </div>
        )}

        {/* Basket Header with Health Metrics */}
        <BasketHeader 
          basketName={basket.name || 'Untitled Basket'} 
          health={health} 
        />

        {/* Maintenance suggestions badge */}
        <div className="-mt-3">
          <a
            href={`/baskets/${id}/maintenance`}
            className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-medium transition-colors ${
              suggestionsCount > 0
                ? 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100'
                : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
            }`}
          >
            🧹 Maintenance {suggestionsCount > 0 ? `• ${suggestionsCount}` : ''}
          </a>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Latest Reflection */}
          <div className="lg:col-span-1">
            <Suspense fallback={<ReflectionCardSkeleton />}>
              <ReflectionCard 
                reflection={recentReflection} 
                basketId={id} 
              />
            </Suspense>
          </div>

          {/* Recent Activity */}
          <div className="lg:col-span-1">
            <Suspense fallback={<RecentActivityCardSkeleton />}>
              <RecentActivityCard 
                dumps={recentDumps}
                timelineEvents={timelineEvents}
                basketId={id}
              />
            </Suspense>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <a
              href={`/baskets/${id}/overview`}
              className="flex flex-col items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <div className="text-2xl mb-2">📝</div>
              <span className="text-sm font-medium text-gray-900">Add Content</span>
            </a>
            <a
              href={`/baskets/${id}/reflections`}
              className="flex flex-col items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <div className="text-2xl mb-2">🧠</div>
              <span className="text-sm font-medium text-gray-900">Reflections</span>
            </a>
            <a
              href={`/baskets/${id}/timeline`}
              className="flex flex-col items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
            >
              <div className="text-2xl mb-2">📊</div>
              <span className="text-sm font-medium text-gray-900">Timeline</span>
            </a>
            <a
              href={`/baskets/${id}/documents`}
              className="flex flex-col items-center p-4 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors"
            >
              <div className="text-2xl mb-2">📄</div>
              <span className="text-sm font-medium text-gray-900">Documents</span>
            </a>
          </div>
        </div>

        {/* Debug Info (development only) */}
        {process.env.NODE_ENV === 'development' && searchParamsObj.debug === 'true' && (
          <div className="bg-gray-900 text-white rounded-lg p-4 text-sm">
            <h3 className="font-bold mb-2">🔍 Debug Info</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <strong>Basket:</strong> {basket.id}<br />
                <strong>Workspace:</strong> {workspace.id}<br />
                <strong>User:</strong> {userId}
              </div>
              <div>
                <strong>Health Score:</strong> {health.activity_score}%<br />
                <strong>Dumps:</strong> {health.dump_count}<br />
                <strong>Reflections:</strong> {health.reflection_count}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Loading skeletons
function ReflectionCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-5 h-5 bg-gray-200 rounded animate-pulse" />
        <div className="w-32 h-5 bg-gray-200 rounded animate-pulse" />
      </div>
      <div className="space-y-3">
        <div className="w-full h-4 bg-gray-200 rounded animate-pulse" />
        <div className="w-3/4 h-4 bg-gray-200 rounded animate-pulse" />
        <div className="w-1/2 h-4 bg-gray-200 rounded animate-pulse" />
      </div>
    </div>
  );
}

function RecentActivityCardSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-5 h-5 bg-gray-200 rounded animate-pulse" />
        <div className="w-32 h-5 bg-gray-200 rounded animate-pulse" />
      </div>
      <div className="space-y-3">
        <div className="w-full h-16 bg-gray-50 rounded-lg animate-pulse" />
        <div className="w-full h-16 bg-gray-50 rounded-lg animate-pulse" />
      </div>
    </div>
  );
}
