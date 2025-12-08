export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { cookies } from "next/headers";
import { createTestAwareClient, getTestAwareAuth, checkMembershipUnlessTest } from "@/lib/auth/testHelpers";
import { z } from "zod";
import { createTimelineEmitter } from "@/lib/canon/TimelineEventEmitter";
import { PipelineBoundaryGuard } from "@/lib/canon/PipelineBoundaryGuard";
import { createGovernedDump } from "@/lib/api/capture";
import type { CaptureRequest } from "@/lib/api/capture";

function normalize(body: any) {
  const b = body ?? {};
  const n = (v: any) => (v === null || v === undefined ? undefined : v);

  return {
    basket_id: b.basket_id ?? b.basketId,
    text_dump: n(b.text_dump ?? b.text),
    file_url: n(b.file_url ?? b.fileUrl),
    meta: n(b.meta ?? b.source_meta),
    dump_request_id: b.dump_request_id ?? b.dumpRequestId ?? b.request_id,
  };
}

const Schema = z
  .object({
    basket_id: z.string().uuid(),
    dump_request_id: z.string().uuid(),
    text_dump: z.string().trim().min(1).optional(),
    file_url: z.string().url().optional(),
    meta: z
      .object({
        client_ts: z.string().optional(),
        ingest_trace_id: z.string().uuid().optional(),
      })
      .catchall(z.unknown())
      .optional(),
  })
  .strict()
  .refine(
    (d) => Boolean(d.text_dump) || Boolean(d.file_url),
    { message: "Provide non-empty text_dump or file_url" }
  );

export async function POST(req: Request) {
  try {
    const raw = await req.json().catch(() => null);
    const parsed = Schema.safeParse(normalize(raw));
    if (!parsed.success) {
      return Response.json({ error: "Invalid request", details: parsed.error.flatten() }, { status: 422 });
    }
    const { basket_id, text_dump, file_url, meta, dump_request_id } = parsed.data;
    
    const supabase = createTestAwareClient({ cookies });
    
    // Pipeline boundary enforcement: P0 Capture
    // This route should only create dumps, no interpretation or processing
    // Agent processing happens asynchronously via queue trigger
    PipelineBoundaryGuard.enforceP0Capture({
      type: 'dump.create',
      payload: { text_dump, file_url },
      context: { basket_id }
    });
    const { userId, isTest } = await getTestAwareAuth(supabase);

    // Resolve basket + workspace
    const { data: basket, error: bErr } = await supabase
      .from("baskets")
      .select("id, workspace_id")
      .eq("id", basket_id)
      .maybeSingle();
    if (bErr) return Response.json({ error: `Basket lookup failed: ${bErr.message}` }, { status: 400 });
    if (!basket) return Response.json({ error: "Basket not found" }, { status: 404 });

    // Verify membership (defense-in-depth; RLS still applies)
    try {
      await checkMembershipUnlessTest(supabase, basket.workspace_id, userId, isTest);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      if (message === 'Forbidden') {
        return Response.json({ error: "Forbidden" }, { status: 403 });
      }
      return Response.json({ error: `Membership check failed: ${message}` }, { status: 400 });
    }

    // GOVERNANCE-COMPLIANT CAPTURE WORKFLOW
    // Route through Decision Gateway per Sacred Principle #1
    const captureRequest: CaptureRequest = {
      basket_id,
      text_dump: text_dump || undefined,
      file_url: file_url || undefined,
      source_meta: meta || undefined
    };

    try {
      const result = await createGovernedDump(
        supabase,
        userId,
        basket.workspace_id,
        captureRequest
      );

      if (result.route === 'direct') {
        // Direct commit succeeded - extract dump_id from result
        // For now, return success without dump_id (UX will handle)
        return Response.json({ 
          success: true,
          route: 'direct',
          message: result.message,
          decision_reason: result.decision_reason
        }, { status: 201 });
      } else {
        // Proposal created - return proposal info
        return Response.json({
          success: true,
          route: 'proposal', 
          proposal_id: result.proposal_id,
          message: result.message,
          decision_reason: result.decision_reason
        }, { status: 202 }); // 202 Accepted for async processing
      }

    } catch (captureError) {
      console.error('Governed capture failed:', captureError);
      return Response.json({ 
        error: "Capture workflow failed", 
        details: captureError instanceof Error ? captureError.message : String(captureError)
      }, { status: 500 });
    }
  } catch (e: any) {
    return Response.json({ error: "Unexpected error", details: String(e?.message ?? e) }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}
