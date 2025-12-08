"use client";

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import CreateBasketDialog from '@/components/CreateBasketDialog';
import BasketActions from '@/components/baskets/BasketActions';

export type BasketSummary = {
  id: string;
  name: string | null;
  status: string | null;
  created_at: string | null;
  pendingProposals: {
    count: number;
    lastCreatedAt: string | null;
    origin: string | null;
    host: string | null;
  };
};

export function BasketsIndexClient({ baskets }: { baskets: BasketSummary[] }) {
  const router = useRouter();
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleUpdate = () => {
    router.refresh(); // Refresh server component data
  };

  const sortedBaskets = useMemo(() => {
    return [...baskets].sort((a, b) => {
      const aDate = a.created_at ? new Date(a.created_at).getTime() : 0;
      const bDate = b.created_at ? new Date(b.created_at).getTime() : 0;
      return bDate - aDate;
    });
  }, [baskets]);

  const hasBaskets = sortedBaskets.length > 0;

  return (
    <div className="space-y-8">
      <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Context Baskets</h1>
          <p className="text-sm text-muted-foreground">
            Curate the baskets that hold your governed knowledge. Once Claude or ChatGPT are connected, ambient captures will land here automatically.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>New basket</Button>
      </header>

      {!hasBaskets ? (
        <section className="rounded-xl border border-dashed border-border bg-muted/20 p-12 text-center">
          <h2 className="text-xl font-semibold">No context baskets yet</h2>
          <p className="mt-3 text-sm text-muted-foreground">
            Create a basket for each product or project. Ambient captures from linked AI hosts will populate the right basket automatically.
          </p>
          <div className="mt-6 flex justify-center">
            <Button onClick={() => setDialogOpen(true)}>Create basket</Button>
          </div>
        </section>
      ) : (
        <section className="grid gap-4 md:grid-cols-2">
          {sortedBaskets.map((basket) => {
            const pending = basket.pendingProposals;
            const pendingLabel = pending.count > 0
              ? `${pending.count} pending · ${pending.host || (pending.origin === 'agent' ? 'ambient' : 'manual')}`
              : 'No pending proposals';

            return (
              <button
                key={basket.id}
                type="button"
                onClick={() => router.push(`/baskets/${basket.id}/overview`)}
                className="group flex w-full flex-col gap-3 rounded-xl border border-border bg-card p-4 text-left transition hover:border-primary hover:shadow-sm"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium">{basket.name || 'Untitled basket'}</h3>
                    <p className="text-sm text-muted-foreground">Curated knowledge hub</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full border border-border px-3 py-1 text-xs uppercase tracking-wide text-muted-foreground">
                      {basket.status ?? 'Active'}
                    </span>
                    <BasketActions
                      basketId={basket.id}
                      basketName={basket.name || 'Untitled basket'}
                      basketStatus={basket.status}
                      onUpdate={handleUpdate}
                    />
                  </div>
                </div>
                <div className="flex flex-col gap-1 text-sm text-muted-foreground">
                  <span>{basket.created_at ? `Created ${new Date(basket.created_at).toLocaleString()}` : 'Creation time unknown'}</span>
                  <span>{pendingLabel}</span>
                </div>
              </button>
            );
          })}
        </section>
      )}

      <CreateBasketDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
