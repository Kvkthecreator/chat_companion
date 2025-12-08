import { NextRequest, NextResponse } from "next/server";
import { apiUrl } from "@/lib/env";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const auth = req.headers.get('authorization');
    const sb = req.headers.get('sb-access-token');
    if (auth) headers['Authorization'] = auth;
    if (sb) headers['sb-access-token'] = sb;

    const upstream = await fetch(apiUrl('/api/p4/document-canon'), {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    const payload = await upstream.text();
    return new NextResponse(payload, {
      status: upstream.status,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('[internal/p4/document-canon] proxy failed', error);
    return NextResponse.json({ error: 'proxy_failed' }, { status: 500 });
  }
}
