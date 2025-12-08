import type { ReactNode } from "react";
import { redirect } from "next/navigation";
import { getServerWorkspace } from "@/lib/workspaces/getServerWorkspace";
import { getBasketServer } from "@/lib/server/baskets";

export default async function BasketLayout({
  params,
  children,
}: {
  params: Promise<{ id: string }>;
  children: ReactNode;
}) {
  const { id } = await params;
  const ws = await getServerWorkspace();
  const basket = await getBasketServer(id, ws.id);
  if (!basket) {
    redirect('/baskets');
  }

  return children;
}
