import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

import { apiUrl } from '@/lib/env';
import { apiPost } from '@/lib/server/http';

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  if (!body || typeof body !== 'object') {
    return NextResponse.json({ ok: false, error: 'invalid_body' }, { status: 400 });
  }

  try {
    const response = await fetch(apiUrl('/api/events/emit'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': request.headers.get('authorization') || '',
        'sb-access-token': request.headers.get('sb-access-token') || '',
      },
      body: JSON.stringify(body),
    });
    const json = await response.json().catch(() => ({}));
    return NextResponse.json(json, { status: response.status });
  } catch (error) {
    console.error('[events/emit] Failed to forward event', error);
    return NextResponse.json({ ok: false, error: 'event_forward_failed' }, { status: 500 });
  }
}
