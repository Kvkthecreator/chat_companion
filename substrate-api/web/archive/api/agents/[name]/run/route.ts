import { NextRequest, NextResponse } from 'next/server';
import { apiUrl } from '@/lib/env';

export async function POST(req: NextRequest, ctx: any) {
  const { name } = ctx.params;
  const body = await req.text();
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  const auth = req.headers.get('authorization');
  if (auth) headers['Authorization'] = auth;
  const cookie = req.headers.get('cookie');
  if (cookie) headers['cookie'] = cookie;
  const res = await fetch(apiUrl(`/api/agents/${name}/run`), {
    method: 'POST',
    headers,
    body,
    cache: 'no-store',
  });
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
