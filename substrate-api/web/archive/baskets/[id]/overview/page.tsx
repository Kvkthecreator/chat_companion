/**
 * Page: /baskets/[id]/overview - Basket Overview (Canon v3.1)
 *
 * Primary basket dashboard showing:
 * - Editable basket title and archive menu
 * - Latest basket-level reflection (insights snapshot)
 * - Key metrics (blocks, documents counts)
 * - Documents list
 *
 * Canon v3.1: Relationships removed (replaced by Neural Map in /graph)
 * Note: Anchors now managed in /building-blocks as substrate metadata
 */
import { cookies } from "next/headers";
import { createServerComponentClient } from "@/lib/supabase/clients";
import { checkBasketAccess } from "@/lib/baskets/access";
import { BasketWrapper } from "@/components/basket/BasketWrapper";
import MemoryClient from "./MemoryClient";
import { hasIdentityGenesis, isBlankBasket } from "@/lib/server/onboarding";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";

interface PageProps {
  params: Promise<{ id: string }>;
  searchParams?: Promise<Record<string, string | undefined>>;
}

export default async function MemoryPage({ params }: PageProps) {
  const { id } = await params;
  const supabase = createServerComponentClient({ cookies });

  // Consolidated authorization and basket access check
  const { basket: basketAccess } = await checkBasketAccess(supabase, id);

  // Fetch full basket data for context (extending the access check data)
  const { data: basketDetails } = await supabase
    .from('baskets')
    .select('description, status, created_at, last_activity_ts, tags, origin_template, name')
    .eq('id', id)
    .maybeSingle();

  // Combine access data with details, using safe defaults for optional fields
  const basket = {
    id: basketAccess.id,
    name: basketDetails?.name ?? basketAccess.name,
    workspace_id: basketAccess.workspace_id,
    description: basketDetails?.description || null,
    status: basketDetails?.status || null,
    created_at: basketDetails?.created_at || new Date().toISOString(),
    last_activity_ts: basketDetails?.last_activity_ts || null,
    tags: basketDetails?.tags || null,
    origin_template: basketDetails?.origin_template || null,
  };

  // Check if user needs onboarding (only if basket blank AND no identity genesis)
  const { userId } = await getAuthenticatedUser(supabase);
  const [blank, hasGenesis] = await Promise.all([
    isBlankBasket(id),
    hasIdentityGenesis(id),
  ]);
  const needsOnboarding = blank && !hasGenesis;

  return (
    <BasketWrapper basket={basket}>
      <div className="space-y-6 pb-8">
        <MemoryClient
          basketId={id}
          basketName={basket.name}
          needsOnboarding={needsOnboarding}
        />
      </div>
    </BasketWrapper>
  );
}
