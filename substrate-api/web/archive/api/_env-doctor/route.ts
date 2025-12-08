import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const report = {
    env: {
      NEXT_PUBLIC_SUPABASE_URL: !!process.env.NEXT_PUBLIC_SUPABASE_URL,
      NEXT_PUBLIC_SUPABASE_ANON_KEY: !!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
      NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL || null,
      NODE_ENV: process.env.NODE_ENV,
    },
  };
  return NextResponse.json(report);
}
