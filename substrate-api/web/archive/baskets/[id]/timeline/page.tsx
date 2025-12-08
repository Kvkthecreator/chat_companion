"use client";

import { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import KnowledgeTimeline from '@/components/timeline/KnowledgeTimeline';
import TimelineUploadsPanel from '@/components/timeline/UploadsPanel';
import { Button } from '@/components/ui/Button';
import { Clock, CloudUpload } from 'lucide-react';

interface TimelinePageProps {
  params: { id: string };
}

export default function TimelinePage({ params }: TimelinePageProps) {
  const { id: basketId } = params;
  const router = useRouter();
  const searchParams = useSearchParams();

  const viewParam = (searchParams.get('view') as 'activity' | 'uploads') || 'activity';
  const highlightUpload = searchParams.get('highlight');

  const [view, setView] = useState<'activity' | 'uploads'>(viewParam);
  const [significance, setSignificance] = useState<'low' | 'medium' | 'high' | undefined>();

  useEffect(() => {
    setView(viewParam);
  }, [viewParam]);

  useEffect(() => {
    if (highlightUpload) {
      setView('uploads');
    }
  }, [highlightUpload]);

  const basePath = useMemo(() => `/baskets/${basketId}/timeline`, [basketId]);

  const updateParams = (nextView: 'activity' | 'uploads', highlight?: string | null) => {
    const params = new URLSearchParams(searchParams.toString());
    if (nextView === 'activity') {
      params.delete('view');
    } else {
      params.set('view', nextView);
    }

    if (highlight) {
      params.set('highlight', highlight);
    } else {
      params.delete('highlight');
    }

    const query = params.toString();
    router.replace(query ? `${basePath}?${query}` : basePath);
    setView(nextView);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b px-4 py-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Knowledge Evolution</h1>
            <p className="text-gray-600">Track how your understanding grows from captures to composed insights.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant={view === 'activity' ? 'default' : 'outline'}
              onClick={() => updateParams('activity')}
            >
              <Clock className="mr-2 h-4 w-4" /> Timeline
            </Button>
            <Button
              size="sm"
              variant={view === 'uploads' ? 'default' : 'outline'}
              onClick={() => updateParams('uploads', highlightUpload)}
            >
              <CloudUpload className="mr-2 h-4 w-4" /> Uploads
            </Button>
          </div>
        </div>

        {view === 'activity' && (
          <div className="mt-3">
            <label className="text-sm font-medium text-gray-700">
              Show
              <select
                value={significance || 'all'}
                onChange={(e) =>
                  setSignificance(
                    e.target.value === 'all'
                      ? undefined
                      : (e.target.value as 'low' | 'medium' | 'high')
                  )
                }
                className="ml-2 rounded border border-gray-300 px-3 py-1 text-sm"
              >
                <option value="all">All milestones</option>
                <option value="high">Major milestones</option>
                <option value="medium">Notable events</option>
                <option value="low">All activity</option>
              </select>
            </label>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto bg-gray-50">
        <div className="mx-auto max-w-5xl space-y-6 p-6">
          {view === 'activity' ? (
            <KnowledgeTimeline basketId={basketId} significance={significance} className="bg-white rounded-lg shadow-sm p-6" />
          ) : (
            <TimelineUploadsPanel basketId={basketId} highlightDumpId={highlightUpload} />
          )}
        </div>
      </div>
    </div>
  );
}
