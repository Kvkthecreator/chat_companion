/**
 * Route: POST /api/baskets/new
 * @contract input  : CreateBasketReq
 * @contract output : CreateBasketRes
 * RLS: workspace-scoped writes
 */
// web/app/api/baskets/new/route.ts
export const runtime = "nodejs"; // avoid Edge so supabase-helpers work
export const dynamic = "force-dynamic";

import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { CreateBasketReqSchema } from "@/lib/schemas/baskets";
import { createHash, randomUUID } from "node:crypto";
import { getServerWorkspace } from "@/lib/workspaces/getServerWorkspace";
import { apiUrl, PUBLIC_API_BASE_URL } from "@/lib/env";

export async function POST(req: NextRequest) {
  await getServerWorkspace();
  const DBG = req.headers.get("x-yarnnn-debug-auth") === "1";
  const requestId = req.headers.get("x-request-id") ?? randomUUID();
  // 1) Parse & validate request (canon: { idempotency_key, basket? })
  let json: unknown;
  try {
    json = await req.json();
  } catch {
    return NextResponse.json(
      { error: { code: "INVALID_JSON", message: "Malformed JSON" } },
      { status: 400 },
    );
  }
  const parsed = CreateBasketReqSchema.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json(
      {
        error: {
          code: "INVALID_INPUT",
          message: "Request failed validation",
          details: parsed.error.flatten(),
        },
      },
      { status: 422 },
    );
  }
  // Try to get token from headers (from fetchWithToken)
  const accessToken =
    req.headers.get("sb-access-token") || req.headers.get("authorization")?.replace("Bearer ", "");

  if (!accessToken) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Missing authentication token" } },
      { status: 401 },
    );
  }

  function redact(token: string) {
    try {
      const [, p] = token.split(".");
      const payload = JSON.parse(Buffer.from(p, "base64").toString());
      return {
        iss: payload.iss,
        aud: payload.aud,
        sub_hash: payload.sub
          ? createHash("sha256").update(payload.sub).digest("hex").slice(0, 8)
          : undefined,
        exp: payload.exp,
        iat: payload.iat,
        aal: payload.aal,
        amr: Array.isArray(payload.amr) ? payload.amr.map((m: any) => m.method) : undefined,
      };
    } catch {
      return {} as Record<string, unknown>;
    }
  }

  // 3) Forward to FastAPI with Bearer token (workspace bootstrap is server-side)
  // Forward canonical payload to FastAPI
  const payload = parsed.data;
  // Debug: Log token info
  if (DBG) {
    console.log("Token forwarding debug:", {
      hasToken: !!accessToken,
      tokenPrefix: accessToken?.substring(0, 20) + "...",
      apiBase: PUBLIC_API_BASE_URL,
      headers: Object.keys(
        req.headers.entries
          ? Array.from(req.headers.entries()).reduce((acc, [k, v]) => ({ ...acc, [k]: v }), {})
          : {},
      ),
    });
  }

  const upstream = await fetch(apiUrl('/api/baskets/new'), {
    method: "POST",
    cache: "no-store",
    headers: {
      "content-type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "sb-access-token": accessToken,
      "x-request-id": requestId,
      ...(DBG ? { "x-yarnnn-debug-auth": "1" } : {}),
    },
    body: JSON.stringify(payload),
  });

  const text = await upstream.text();
  if (!upstream.ok && DBG) {
    return NextResponse.json(
      { error: { code: "UPSTREAM", message: "Auth failed" }, debug: redact(accessToken) },
      { status: upstream.status },
    );
  }

  return new NextResponse(text, { status: upstream.status });
}
