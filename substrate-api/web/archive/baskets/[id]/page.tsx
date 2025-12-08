/**
 * Redirect: /baskets/[id] -> /baskets/[id]/overview
 * Status: 302 Temporary Redirect (overview is primary operating surface)
 */
import { redirect } from "next/navigation";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function BasketPage({ params }: Props) {
  const { id } = await params;
  redirect(`/baskets/${id}/overview`);
}
