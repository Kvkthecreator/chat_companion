# /baskets/[id]/memory – Wiring

Data Flow
- fetchProjection() -> GET /api/baskets/:id/projection -> ReflectionDTO

SWR Keys / Invalidation (if SWR used)
- No SWR used (server-side fetch with no-store cache)

Contracts
- ReflectionDTO (pattern, tension, question)

Components
- DashboardClient (renders projection data)
- ReflectionCards (renders pattern, tension, question)