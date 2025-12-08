export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createTestAwareClient, getTestAwareAuth } from "@/lib/auth/testHelpers";
import { z } from "zod";

/**
 * P3 Insight Canon Generation API
 *
 * Proxies to backend P3 insights service for generating basket-level insights.
 * Direct operation (not governed per Canon v3.1).
 */

const InsightCanonRequestSchema = z.object({
  basket_id: z.string().uuid(),
  force: z.boolean().default(false),
  agent_context: z.record(z.any()).optional()
});

export async function POST(req: NextRequest) {
  try {
    const raw = await req.json().catch(() => null);
    const parsed = InsightCanonRequestSchema.safeParse(raw);

    if (!parsed.success) {
      return NextResponse.json({
        error: "Invalid insight generation request",
        details: parsed.error.flatten()
      }, { status: 422 });
    }

    const { basket_id, force, agent_context } = parsed.data;
    const supabase = createTestAwareClient({ cookies });
    const { userId, isTest } = await getTestAwareAuth(supabase);

    if (!userId && !isTest) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Verify basket access
    const { data: basket } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basket_id)
      .single();

    if (!basket) {
      return NextResponse.json({ error: "Basket not found or access denied" }, { status: 404 });
    }

    // Call backend P3 insights service
    const backendResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/p3/insight-canon`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`
      },
      body: JSON.stringify({
        basket_id,
        force,
        agent_context
      })
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}));
      return NextResponse.json({
        error: "Failed to generate insight",
        details: errorData.detail || errorData.message || backendResponse.statusText
      }, { status: backendResponse.status });
    }

    const result = await backendResponse.json();

    return NextResponse.json(result, { status: 200 });

  } catch (error) {
    console.error('P3 insight generation error:', error);
    return NextResponse.json({
      error: "Insight generation failed",
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}
