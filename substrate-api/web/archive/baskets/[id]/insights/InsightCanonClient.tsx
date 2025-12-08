"use client";

import { useState, useEffect } from 'react';
import { createBrowserClient } from '@/lib/supabase/clients';
import InsightCanonCard from '@/components/insights/InsightCanonCard';
import { Clock, GitBranch, Database, Sparkles } from 'lucide-react';

interface InsightCanonClientProps {
  basketId: string;
}

interface InsightHistory {
  id: string;
  reflection_text: string;
  created_at: string;
  substrate_hash: string;
  is_current: boolean;
}

interface DerivedSource {
  type: string;
  count: number;
}

export default function InsightCanonClient({ basketId }: InsightCanonClientProps) {
  const supabase = createBrowserClient();
  const [history, setHistory] = useState<InsightHistory[]>([]);
  const [derivedSources, setDerivedSources] = useState<DerivedSource[]>([]);
  const [loadingStats, setLoadingStats] = useState(true);

  async function loadInsightStats() {
    try {
      setLoadingStats(true);

      // Load version history (last 5 versions)
      const { data: historyData } = await supabase
        .from('reflections_artifact')
        .select('id, reflection_text, created_at, substrate_hash, is_current')
        .eq('basket_id', basketId)
        .eq('insight_type', 'insight_canon')
        .order('created_at', { ascending: false })
        .limit(5);

      if (historyData) setHistory(historyData);

      // Load substrate counts for "derived from" section
      const [blocks, dumps, events] = await Promise.all([
        supabase.from('blocks').select('id', { count: 'exact', head: true })
          .eq('basket_id', basketId)
          .in('state', ['ACCEPTED', 'LOCKED', 'CONSTANT']),
        supabase.from('raw_dumps').select('id', { count: 'exact', head: true })
          .eq('basket_id', basketId),
        supabase.from('timeline_events').select('id', { count: 'exact', head: true })
          .eq('basket_id', basketId)
      ]);

      setDerivedSources([
        { type: 'Blocks', count: blocks.count || 0 },
        { type: 'Dumps', count: dumps.count || 0 },
        { type: 'Events', count: events.count || 0 }
      ]);
    } catch (err) {
      console.error('Failed to load insight stats:', err);
    } finally {
      setLoadingStats(false);
    }
  }

  useEffect(() => {
    loadInsightStats();
  }, [basketId]);

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-purple-600" />
          Insight Canon
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Your basket's core understanding of what matters now
        </p>
      </div>

      {/* Current insight */}
      <InsightCanonCard
        basketId={basketId}
        compact={false}
        onInsightGenerated={loadInsightStats}
      />

      {/* Two-column layout for stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Substrate sources */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center gap-2 mb-4">
            <Database className="h-5 w-5 text-gray-600" />
            <h3 className="font-semibold text-gray-900">Derived From</h3>
          </div>
          {loadingStats ? (
            <div className="text-sm text-gray-500">Loading...</div>
          ) : (
            <div className="space-y-3">
              {derivedSources.map(source => (
                <div key={source.type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-700">{source.type}</span>
                  <span className="text-sm font-mono font-semibold text-purple-600">
                    {source.count}
                  </span>
                </div>
              ))}
              <div className="pt-3 border-t border-gray-100 text-xs text-gray-500">
                Insight synthesizes all accepted substrate in this basket
              </div>
            </div>
          )}
        </div>

        {/* Version history */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center gap-2 mb-4">
            <GitBranch className="h-5 w-5 text-gray-600" />
            <h3 className="font-semibold text-gray-900">Version History</h3>
          </div>
          {loadingStats ? (
            <div className="text-sm text-gray-500">Loading...</div>
          ) : history.length === 0 ? (
            <div className="text-sm text-gray-500">No history yet</div>
          ) : (
            <div className="space-y-2">
              {history.map((version, idx) => (
                <div
                  key={version.id}
                  className={`flex items-start gap-2 p-2 rounded ${
                    version.is_current ? 'bg-purple-50 border border-purple-200' : 'hover:bg-gray-50'
                  }`}
                >
                  <Clock className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">
                        {new Date(version.created_at).toLocaleDateString()}
                      </span>
                      {version.is_current && (
                        <span className="text-xs font-medium text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded">
                          Current
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 truncate mt-0.5">
                      {version.reflection_text.substring(0, 60)}...
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
