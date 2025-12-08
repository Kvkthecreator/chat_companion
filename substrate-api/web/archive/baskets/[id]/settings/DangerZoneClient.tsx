"use client";

import { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { notificationAPI } from '@/lib/api/notifications';

interface Props {
  basketId: string;
  basketName: string;
}

type Mode = 'archive_all' | 'redact_dumps';

export default function DangerZoneClient({ basketId, basketName }: Props) {
  const [loading, setLoading] = useState(true);
  const [counts, setCounts] = useState<{ blocks: number; dumps: number } | null>(null);
  const [mode, setMode] = useState<Mode>('archive_all');
  const [confirm, setConfirm] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/baskets/${basketId}/purge/preview`, { cache: 'no-store' });
        if (res.ok) {
          setCounts(await res.json());
        } else {
          setCounts(null);
        }
      } catch {
        setCounts(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [basketId]);

  const disabled = useMemo(() => confirm !== basketName, [confirm, basketName]);

  const run = async () => {
    setSubmitting(true);
    setResult(null);
    const correlationId = `basket-${basketId}-purge-${Date.now()}`;

    await notificationAPI.emitJobStarted('basket.purge', `Purging “${basketName}”`, {
      basketId,
      correlationId,
    });

    try {
      const res = await fetch(`/api/baskets/${basketId}/purge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode, confirmation_text: confirm })
      });
      const json = await res.json();
      setResult(json);
      if (res.ok) {
        await notificationAPI.emitJobSucceeded('basket.purge', 'Purge completed', {
          basketId,
          correlationId,
          payload: {
            operations: json.total_operations,
            batches: json.executed_batches,
          },
        });
        // refresh counts
        const pv = await fetch(`/api/baskets/${basketId}/purge/preview`, { cache: 'no-store' });
        if (pv.ok) setCounts(await pv.json());
      } else {
        const errorMessage = json?.error || 'Purge failed';
        await notificationAPI.emitJobFailed('basket.purge', errorMessage, {
          basketId,
          correlationId,
          error: errorMessage,
        });
      }
    } catch (e) {
      setResult({ error: 'Network error' });
      await notificationAPI.emitJobFailed('basket.purge', 'Network error during purge', {
        basketId,
        correlationId,
        error: e instanceof Error ? e.message : 'network_error',
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Overview</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">
          {loading ? (
            <div className="text-muted-foreground">Loading…</div>
          ) : counts ? (
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant="outline">Blocks {counts.blocks}</Badge>
              <Badge variant="outline">Dumps {counts.dumps}</Badge>
            </div>
          ) : (
            <div className="text-red-600">Failed to load counts</div>
          )}
        </CardContent>
      </Card>

      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="text-red-700">Danger Zone</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm">
              <input type="radio" name="mode" checked={mode==='archive_all'} onChange={() => setMode('archive_all')} />
              <span>Delete All — Archive + Redact All</span>
            </label>
            <div className="pl-6 text-xs text-muted-foreground">Archives blocks and redacts raw dumps. Archived items may be auto‑deleted later by retention policy.</div>

            <label className="flex items-center gap-2 text-sm mt-2">
              <input type="radio" name="mode" checked={mode==='redact_dumps'} onChange={() => setMode('redact_dumps')} />
              <span>Redact Dumps Only</span>
            </label>
            <div className="pl-6 text-xs text-muted-foreground">Deletes raw dumps (original notes) only. Leaves meaning intact.</div>
          </div>

          <div className="pt-2">
            <div className="text-sm font-medium">Type the basket name to confirm</div>
            <input
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder={basketName}
              className="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm"
            />
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={run} disabled={disabled || submitting} className="bg-red-600 hover:bg-red-700 text-white">
              {submitting ? 'Working…' : mode==='redact_dumps' ? 'Delete Dumps' : 'Delete All'}
            </Button>
            {result && (
              <div className="text-xs text-muted-foreground">
                {result.error ? (
                  <span className="text-red-600">{result.error}</span>
                ) : (
                  <span>Executed: {result.executed_batches || 0} batches, ops {result.total_operations || 0}</span>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
