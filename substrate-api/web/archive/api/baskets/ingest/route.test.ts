import { test, expect, vi } from 'vitest';

function createRequest(body: any) {
  return { json: async () => body } as any;
}

vi.mock('@/lib/server/auth', () => ({
  getAuthenticatedUser: vi.fn(),
  ensureWorkspaceForUser: vi.fn()
}));
vi.mock('@/lib/server/ingest', () => ({
  ingestBasketAndDumps: vi.fn()
}));

test('POST /api/baskets/ingest success', async () => {
  const body = {
    idempotency_key: '11111111-1111-1111-1111-111111111111',
    basket: { name: 'Basket' },
    dumps: [
      { dump_request_id: '22222222-2222-2222-2222-222222222222', text_dump: 'A' },
      { dump_request_id: '33333333-3333-3333-3333-333333333333', text_dump: 'B' }
    ]
  };
  const req = createRequest(body);

  const auth = await import('@/lib/server/auth');
  const ingest = await import('@/lib/server/ingest');
  auth.getAuthenticatedUser.mockResolvedValue({ userId: 'user-1' });
  auth.ensureWorkspaceForUser.mockResolvedValue('ws-1');
  ingest.ingestBasketAndDumps.mockResolvedValue({
    raw: {
      basket_created: true,
      dumps: [{ dump_created: true }, { dump_created: false }]
    },
    data: {
      basket_id: 'basket-1',
      dumps: [{ dump_id: 'dump-a' }, { dump_id: 'dump-b' }]
    }
  });
  const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

  const { POST } = await import('./route');
  const res = await POST(req);
  expect(res.status).toBe(200);
  const json = await res.json();
  expect(json.basket_id).toBe('basket-1');
  expect(json.dumps).toEqual([{ dump_id: 'dump-a' }, { dump_id: 'dump-b' }]);

  expect(logSpy).toHaveBeenCalledTimes(2);
  const first = JSON.parse(logSpy.mock.calls[0][0]);
  const second = JSON.parse(logSpy.mock.calls[1][0]);
  expect(first.request_id).toBeTruthy();
  expect(second.request_id).toBe(first.request_id);
  expect(second.dumps).toEqual([
    { dump_request_id: '22222222-2222-2222-2222-222222222222', action: 'created' },
    { dump_request_id: '33333333-3333-3333-3333-333333333333', action: 'replayed' }
  ]);

  logSpy.mockRestore();
  vi.resetModules();
});

test('POST /api/baskets/ingest validation error', async () => {
  const req = createRequest({});
  const auth = await import('@/lib/server/auth');
  auth.getAuthenticatedUser.mockResolvedValue({ userId: 'user-1' });
  auth.ensureWorkspaceForUser.mockResolvedValue('ws-1');
  const logSpy = vi.spyOn(console, 'log').mockImplementation(() => {});

  const { POST } = await import('./route');
  const res = await POST(req);
  expect(res.status).toBe(422);
  const json = await res.json();
  expect(json.error.code).toBe('INVALID_INPUT');

  expect(logSpy).not.toHaveBeenCalled();
  logSpy.mockRestore();
  vi.resetModules();
});
