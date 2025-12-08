import { NextRequest, NextResponse } from "next/server";
import { apiUrl } from "@/lib/env";

export async function POST(request: NextRequest) {
  // ① copy incoming body
  const body = await request.text();

  // ② Forward BOTH the Authorization header and the Supabase cookie.
  //    FastAPI validates either one, and RSC/Route Handlers strip auth headers automatically.
  const headers: HeadersInit = { "Content-Type": "application/json" };
  const auth = request.headers.get("authorization");
  if (auth) headers["Authorization"] = auth; // capital-A
  const cookie = request.headers.get("cookie");
  if (cookie) headers["cookie"] = cookie; // pass Supabase session cookie

  // ③ proxy to backend
  const res = await fetch(apiUrl("/api/agent-run"), {
    method: "POST",
    headers,
    body,
    cache: "no-store",
  });

  const json = await res.json();
  return NextResponse.json(json, { status: res.status });
}