import { SubpageHeader } from "@/components/basket/SubpageHeader";
import { RequestBoundary } from "@/components/RequestBoundary";
import dynamic from 'next/dynamic';

const InsightCanonClient = dynamic(() => import('./InsightCanonClient'), {
  loading: () => (
    <div className="space-y-4">
      <div className="animate-pulse bg-gray-100 h-32 rounded-lg"></div>
      <div className="animate-pulse bg-gray-100 h-24 rounded-lg"></div>
    </div>
  ),
});

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function InsightsPage({ params }: PageProps) {
  const { id } = await params;

  return (
    <RequestBoundary>
      <div className="flex h-full flex-col">
        <div className="border-b p-4">
          <SubpageHeader
            title="Insight Canon"
            basketId={id}
            description="Your basket's core understanding of what matters now"
          />
        </div>
        <div className="flex-1 overflow-y-auto bg-gray-50">
          <div className="mx-auto max-w-4xl">
            <div className="p-6">
              <InsightCanonClient basketId={id} />
            </div>
          </div>
        </div>
      </div>
    </RequestBoundary>
  );
}
