import { NextResponse } from "next/server";
import { cookies, headers } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const h = await headers();
  const host = h.get("host");
  const cookieStore = await cookies();
  const names = cookieStore.getAll().map((c) => c.name);
  const hasSb = names.some((n) => n.startsWith("sb-") || n.includes("supabase"));

  const supabase = createRouteHandlerClient({ cookies });
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  return NextResponse.json({
    host,
    cookieSample: names.slice(0, 5),
    hasSupabaseCookies: hasSb,
    userPresent: !!user,
    authError: error?.message ?? null,
  });
}
