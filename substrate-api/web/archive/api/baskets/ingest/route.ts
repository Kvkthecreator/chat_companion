/**
 * Route: POST /api/baskets/ingest
 * @contract input  : IngestReq
 * @contract output : IngestRes
 * RLS: workspace-scoped writes
 */
import { NextRequest, NextResponse } from 'next/server';
import { randomUUID } from 'crypto';
import { z } from 'zod';
import { IngestReqSchema } from '@/lib/schemas/ingest';
import { getAuthenticatedUser, ensureWorkspaceForUser } from '@/lib/server/auth';
import { ingestBasketAndDumps } from '@/lib/server/ingest';

export async function POST(req: NextRequest) {
  const requestId = randomUUID();
  try {
    const { userId, token } = await getAuthenticatedUser(req);
    const workspaceId = await ensureWorkspaceForUser(userId, token);
    const body = IngestReqSchema.parse(await req.json());
    const { raw, data } = await ingestBasketAndDumps({
      workspaceId,
      userId,
      idempotency_key: body.idempotency_key,
      basket: body.basket,
      dumps: body.dumps,
      batch_id: body.batch_id,
      comprehensive_review: body.comprehensive_review,
      token,
    });
    // Log request and response separately per canon - no field synthesis
    console.log(
      JSON.stringify({
        route: '/api/baskets/ingest',
        request_id: requestId,
        user_id: userId,
        workspace_id: workspaceId,
        request: {
          idempotency_key: body.idempotency_key,
          basket: body.basket,
          dumps_count: body.dumps.length
        }
      })
    );
    console.log(
      JSON.stringify({
        route: '/api/baskets/ingest',
        request_id: requestId,
        user_id: userId,
        workspace_id: workspaceId,
        idempotency_key: body.idempotency_key,
        basket: raw && (raw as any).basket_created ? 'created' : 'replayed',
        dumps: (raw as any)?.dumps?.map((d: any, i: number) => ({
          dump_request_id: body.dumps[i]?.dump_request_id,
          action: d.dump_created ? 'created' : 'replayed'
        })) ?? []
      })
    );
    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    if (err instanceof z.ZodError) {
      return NextResponse.json(
        {
          error: {
            code: 'INVALID_INPUT',
            message: err.message,
            details: err.flatten ? err.flatten() : err.issues
          }
        },
        { status: 422 }
      );
    }
    if (err instanceof Error && err.message === 'Unauthorized') {
      return NextResponse.json(
        {
          error: { code: 'UNAUTHORIZED', message: 'Unauthorized', details: {} }
        },
        { status: 401 }
      );
    }
    console.error('ingest route error', err);
    return NextResponse.json(
      {
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Internal Server Error',
          details: {}
        }
      },
      { status: 500 }
    );
  }
}
