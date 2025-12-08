/**
 * Basket Change Requests Page
 *
 * Canon: YARNNN_GOVERNANCE_CANON_V5.md
 * Shows basket-level change requests (Type 2: basket-scoped substrate mutations)
 */
import type { Metadata } from 'next';
import dynamic from 'next/dynamic';
import { RequestBoundary } from '@/components/RequestBoundary';
import { SubpageHeader } from '@/components/basket/SubpageHeader';

const BasketChangeRequestsClient = dynamic(() => import('./BasketChangeRequestsClient'), {
  loading: () => (
    <div className="space-y-4">
      <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
      <div className="h-24 animate-pulse rounded-lg bg-gray-100" />
    </div>
  ),
});

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  return {
    title: `Change Requests - Basket ${id}`,
    description: 'Review and approve basket substrate change proposals',
  };
}

export default async function BasketChangeRequestsPage({ params }: PageProps) {
  const { id: basketId } = await params;
  
  return (
    <RequestBoundary>
      <div className="flex h-full flex-col">
        <div className="border-b border-gray-100 p-3">
          <SubpageHeader
            title="Change Requests"
            description="Govern substrate proposals for this basket"
            basketId={basketId}
          />
        </div>
        <div className="flex-1 overflow-y-auto bg-gray-50">
          <div className="mx-auto max-w-6xl">
            <div className="p-4">
              <BasketChangeRequestsClient basketId={basketId} />
            </div>
          </div>
        </div>
      </div>
    </RequestBoundary>
  );
}
