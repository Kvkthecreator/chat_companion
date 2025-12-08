export const runtime = "nodejs";

import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { createHash, randomUUID } from "node:crypto";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";
import { apiUrl } from "@/lib/env";

function hash(v: string) {
  return createHash("sha256").update(v).digest("hex").slice(0, 8);
}

function safeDecode(token?: string) {
  try {
    if (!token) return { tokenClaims: {} };
    const [, p] = token.split(".");
    const payload = JSON.parse(Buffer.from(p, "base64").toString());
    return {
      tokenClaims: {
        iss: payload.iss,
        aud: payload.aud,
        sub_hash: payload.sub ? hash(payload.sub) : undefined,
        exp: payload.exp,
        iat: payload.iat,
        aal: payload.aal,
        amr: Array.isArray(payload.amr)
          ? payload.amr.map((m: any) => m.method)
          : undefined,
      },
    };
  } catch {
    return { tokenClaims: {} };
  }
}

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(req: NextRequest, ctx: RouteContext) {
  const { id: basketId } = await ctx.params;
  const DBG = req.headers.get("x-yarnnn-debug-auth") === "1";
  const supabase = createRouteHandlerClient({ cookies });
  await getAuthenticatedUser(supabase);
  const accessToken =
    req.headers.get("sb-access-token") ||
    req.headers.get("authorization")?.replace("Bearer ", "");
  if (!accessToken) {
    return NextResponse.json(
      { error: { code: "UNAUTHORIZED", message: "Missing authentication" } },
      { status: 401 }
    );
  }
  const requestId = req.headers.get("x-request-id") ?? randomUUID();
  const res = await fetch(apiUrl(`/api/baskets/${basketId}/deltas`), {
    method: "GET",
    cache: "no-store",
    headers: {
      "content-type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      "sb-access-token": accessToken,
      "x-request-id": requestId,
      ...(DBG ? { "x-yarnnn-debug-auth": "1" } : {}),
    },
  });
  const text = await res.text();
  if (!res.ok && DBG) {
    return NextResponse.json(
      { error: { code: "UPSTREAM", message: "Upstream error" }, debug: safeDecode(accessToken).tokenClaims },
      { status: res.status }
    );
  }
  return new NextResponse(text, { status: res.status });
}
