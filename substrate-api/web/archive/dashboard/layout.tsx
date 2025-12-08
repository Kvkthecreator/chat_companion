// File: /app/dashboard/layout.tsx

import type { ReactNode } from "react";
import { cookies } from "next/headers";
import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import type { Database } from "@/lib/dbTypes";
import ClientLayoutWrapper from "@/components/layouts/ClientLayoutWrapper";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";

export default async function DashboardLayout({ children }: { children: ReactNode }) {
  const supabase = createServerComponentClient<Database>({ cookies });
  await getAuthenticatedUser(supabase);

  return (
    <ClientLayoutWrapper initialSession={null}>
      {children}
    </ClientLayoutWrapper>
  );
}
