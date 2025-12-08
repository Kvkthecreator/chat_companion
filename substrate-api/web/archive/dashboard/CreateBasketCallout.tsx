"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import CreateBasketDialog from '@/components/CreateBasketDialog';
import { cn } from '@/lib/utils';

export function CreateBasketCallout({ className }: { className?: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div
      className={cn(
        'rounded-xl border border-dashed border-border bg-muted/30 p-10 text-center',
        className
      )}
    >
      <h3 className="text-xl font-semibold">Build your first basket</h3>
      <p className="mt-3 text-sm text-muted-foreground">
        Baskets organise blocks for each product or project. Create one now and connected hosts will
        file new blocks in the right place automatically.
      </p>
      <div className="mt-6 flex justify-center">
        <Button onClick={() => setOpen(true)}>Create basket</Button>
      </div>
      <CreateBasketDialog open={open} onOpenChange={setOpen} />
    </div>
  );
}
