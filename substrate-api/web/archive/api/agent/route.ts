import { NextRequest, NextResponse } from "next/server";
import { apiUrl } from "@/lib/env";

/**
 * Proxy POST /api/agent to the backend FastAPI /agent endpoint,
 * forwarding headers and body.
 */
export async function POST(request: NextRequest) {
  // Read raw body
  const body = await request.text();
  // Logging incoming proxy request
  console.log("[🔀 proxy /api/agent] Incoming request body:", body);
  // Forward auth headers and cookies
  const headers: HeadersInit = { "Content-Type": "application/json" };
  const auth = request.headers.get("authorization");
  if (auth) headers["Authorization"] = auth;
  const cookie = request.headers.get("cookie");
  if (cookie) headers["cookie"] = cookie;
  // Backend URL
  const res = await fetch(apiUrl("/api/agent"), {
    method: "POST",
    headers,
    body,
    cache: "no-store",
  });
  // Log upstream response status
  console.log("[🔀 proxy /api/agent] Upstream response status:", res.status);
  const data = await res.json();
  // Log upstream response body
  console.log("[🔀 proxy /api/agent] Upstream response body:", data);
  return NextResponse.json(data, { status: res.status });
}