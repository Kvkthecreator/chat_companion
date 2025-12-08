"use client";

import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { notificationService } from '@/lib/notifications/service';

interface CandidatePreview {
  id: string;
  preview: { refs_detached_count: number; relationships_pruned_count: number; affected_documents_count: number };
}

interface SuggestResponse {
  candidates: {
    blocks_to_archive: CandidatePreview[];
    context_items_to_deprecate: string[];
    dumps_to_redact: CandidatePreview[];
    context_item_duplicates?: { label: string; ids: string[] }[];
  }
}

export function MaintenanceClient({ basketId, canEdit }: { basketId: string; canEdit: boolean }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SuggestResponse | null>(null);
  const [selectedBlocks, setSelectedBlocks] = useState<Record<string, boolean>>({});
  const [selectedItems, setSelectedItems] = useState<Record<string, boolean>>({});
  const [selectedDumps, setSelectedDumps] = useState<Record<string, boolean>>({});
  const [selectedDupGroups, setSelectedDupGroups] = useState<Record<string, boolean>>({});
  const [dupCanonical, setDupCanonical] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    refresh();
  }, [basketId]);

  const refresh = async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch(`/api/maintenance/suggest/${basketId}`);
      if (!res.ok) throw new Error('Failed to fetch suggestions');
      const json: SuggestResponse = await res.json();
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
      setData(null);
    } finally { setLoading(false); }
  };

  const toggle = (map: Record<string, boolean>, setMap: (m: Record<string, boolean>) => void, id: string) => {
    const next = { ...map };
    next[id] = !next[id];
    setMap(next);
  };

  const propose = async () => {
    if (!data) return;
    setSubmitting(true);
    try {
      const ops: any[] = [];
      Object.entries(selectedBlocks).forEach(([id, sel]) => { if (sel) ops.push({ type: 'ArchiveBlock', data: { block_id: id } }); });
      Object.entries(selectedDumps).forEach(([id, sel]) => { if (sel) ops.push({ type: 'RedactDump', data: { dump_id: id, scope: 'full', reason: 'maintenance_suggestion' } }); });
      Object.entries(selectedItems).forEach(([id, sel]) => { if (sel) ops.push({ type: 'ArchiveContextItem', data: { context_item_id: id } }); });
      // For duplicates: merge extra ids into the first id as canonical
      (data.candidates.context_item_duplicates || []).forEach(g => {
        if (selectedDupGroups[g.label]) {
          if (g.ids.length > 1) {
            const canonical = dupCanonical[g.label] || g.ids[0];
            const from_ids = g.ids.slice(1);
            ops.push({ type: 'MergeContextItems', data: { from_ids, canonical_id: canonical } });
          }
        }
      });

      if (ops.length === 0) {
        notificationService.notify({ type: 'system.user.action_required', title: 'Select Items', message: 'No items selected to propose', severity: 'warning' });
        setSubmitting(false);
        return;
      }

      const res = await fetch('/api/work', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          work_type: 'MANUAL_EDIT',
          work_payload: { operations: ops, basket_id: basketId },
          priority: 'normal'
        })
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.error || 'Failed to propose');
      if (json.execution_mode === 'auto_execute') {
        notificationService.notify({ type: 'work.completed', title: 'Maintenance Executed', message: `${ops.length} change(s) applied`, severity: 'success' });
      } else {
        notificationService.notify({ type: 'governance.approval.required', title: 'Maintenance Proposed', message: `${ops.length} change(s) awaiting approval`, severity: 'warning' });
      }
      // reset selections
      setSelectedBlocks({}); setSelectedItems({}); setSelectedDumps({});
      setSelectedDupGroups({});
      refresh();
    } catch (e) {
      notificationService.notify({ type: 'system.conflict.detected', title: 'Proposal Failed', message: e instanceof Error ? e.message : 'Failed to propose', severity: 'error' });
    } finally { setSubmitting(false); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Maintenance Suggestions</h2>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={refresh} disabled={loading}>Refresh</Button>
          <Button onClick={propose} disabled={submitting || !canEdit}>{submitting ? 'Submitting…' : 'Propose Selected'}</Button>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center">Loading…</div>
      ) : error ? (
        <div className="p-12 text-center text-red-600">{error}</div>
      ) : !data ? (
        <div className="p-12 text-center">No data</div>
      ) : (
        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Blocks to Archive</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {data.candidates.blocks_to_archive.length === 0 && <div className="text-gray-500">None</div>}
              {data.candidates.blocks_to_archive.map(c => (
                <label key={c.id} className="flex items-center justify-between gap-2 border rounded p-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={!!selectedBlocks[c.id]} onChange={() => toggle(selectedBlocks, setSelectedBlocks, c.id)} />
                    <span>Block {c.id.slice(0,8)}…</span>
                  </div>
                  <div className="flex gap-1">
                    <Badge variant="outline">Refs {c.preview.refs_detached_count}</Badge>
                    <Badge variant="outline">Rels {c.preview.relationships_pruned_count}</Badge>
                    <Badge variant="outline">Docs {c.preview.affected_documents_count}</Badge>
                  </div>
                </label>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Context Items to Deprecate</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {data.candidates.context_items_to_deprecate.length === 0 && <div className="text-gray-500">None</div>}
              {data.candidates.context_items_to_deprecate.map(id => (
                <label key={id} className="flex items-center gap-2 border rounded p-2">
                  <input type="checkbox" checked={!!selectedItems[id]} onChange={() => toggle(selectedItems, setSelectedItems, id)} />
                  <span>Item {id.slice(0,8)}…</span>
                </label>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Dumps to Redact</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {data.candidates.dumps_to_redact.length === 0 && <div className="text-gray-500">None</div>}
              {data.candidates.dumps_to_redact.map(c => (
                <label key={c.id} className="flex items-center justify-between gap-2 border rounded p-2">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" checked={!!selectedDumps[c.id]} onChange={() => toggle(selectedDumps, setSelectedDumps, c.id)} />
                    <span>Dump {c.id.slice(0,8)}…</span>
                  </div>
                  <div className="flex gap-1">
                    <Badge variant="outline">Refs {c.preview.refs_detached_count}</Badge>
                    <Badge variant="outline">Rels {c.preview.relationships_pruned_count}</Badge>
                    <Badge variant="outline">Docs {c.preview.affected_documents_count}</Badge>
                  </div>
                </label>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Context Item Duplicates</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {(!data.candidates.context_item_duplicates || data.candidates.context_item_duplicates.length === 0) && <div className="text-gray-500">None</div>}
              {(data.candidates.context_item_duplicates || []).map(g => (
                <div key={g.label} className="border rounded p-2 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <label className="flex items-center gap-2">
                      <input type="checkbox" checked={!!selectedDupGroups[g.label]} onChange={() => toggle(selectedDupGroups, setSelectedDupGroups, g.label)} />
                      <span className="truncate max-w-[220px]" title={g.label}>{g.label}</span>
                    </label>
                    <Badge variant="outline">{g.ids.length} items</Badge>
                  </div>
                  {selectedDupGroups[g.label] && (
                    <div className="pl-6 space-y-1">
                      <div className="text-xs text-gray-600">Choose canonical item</div>
                      <div className="grid grid-cols-1 gap-1">
                        {g.ids.map(id => (
                          <label key={id} className="flex items-center gap-2 text-xs">
                            <input
                              type="radio"
                              name={`canon:${g.label}`}
                              checked={(dupCanonical[g.label] || g.ids[0]) === id}
                              onChange={() => setDupCanonical(prev => ({ ...prev, [g.label]: id }))}
                            />
                            <span className="font-mono">{id.slice(0,8)}…</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default MaintenanceClient;
