# YARNNN v4.0 Mono-Repo Deployment Guide (Phase 2: Architecture Refactor)

## Overview

YARNNN v4.0 mono-repo follows a **Backend-for-Frontend (BFF)** architecture pattern with clear domain separation:

1. **Work Platform API** (`work-platform/api/`) - Consumer/Work-Facing Application (BFF Layer)
2. **Substrate API** (`substrate-api/api/`) - P0-P4 Agent Pipeline + Memory/Context Domain
3. **Infrastructure** (`infra/`) - Pure utilities (auth, DB clients, shared types)
4. **ChatGPT App** (`mcp-server/adapters/openai-apps/`) - OpenAI GPT integration

## Architecture Principles

### Backend-for-Frontend (BFF) Pattern
- **Work Platform API** is the consumer/work-facing application (to-be-built)
- **Substrate API** contains P0-P4 agent pipeline + memory/context domain
- Work Platform calls Substrate via HTTP (Phase 3) - no direct substrate DB access
- Both services use `infra/` for shared utilities only

### Domain Separation
- **Work Platform Domain**: Consumer/work-facing features, business logic
- **Substrate Domain**: P0-P4 agent pipeline, memory blocks, documents, embeddings, work orchestration
- **Infrastructure**: Authentication, database clients, JWT utilities

## Render Deployment (APIs)

The `render.yaml` configuration defines three services:

### Work Platform API (BFF Layer - Consumer-Facing)
- **Service name**: `yarnnn-work-platform-api`
- **Root directory**: `work-platform/api/`
- **Build command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start command**: `uvicorn src.app.agent_server:app --host 0.0.0.0 --port 10000 --log-level debug`
- **Environment variables**:
  - OPENAI_API_KEY
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY
  - DATABASE_URL
  - SUBSTRATE_API_URL
  - SUBSTRATE_SERVICE_SECRET

### Substrate API (P0-P4 Pipeline + Memory Domain)
- **Service name**: `yarnnn-substrate-api`
- **Root directory**: `substrate-api/api/`
- **Build command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start command**: `uvicorn src.app.agent_server:app --host 0.0.0.0 --port 10000 --log-level debug`
- **Environment variables**:
  - OPENAI_API_KEY
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY
  - DATABASE_URL
  - MCP_SHARED_SECRET (for ChatGPT/Claude integration)
  - ENABLE_SERVICE_AUTH (optional)
  - SUBSTRATE_SERVICE_SECRET (optional)
  - ALLOWED_SERVICES (optional)

### ChatGPT App (MCP Integration)
- **Service name**: `yarnnn-chatgpt-app`
- **Root directory**: `mcp-server/adapters/openai-apps/`
- **Runtime**: Node.js
- See render.yaml for full configuration

## Vercel Deployment (Web Frontends)

### Work Platform Web
- **Root directory**: `work-platform/web/`
- **Framework**: Next.js (auto-detected)
- **Build command**: `npm run build` (auto)
- **Output directory**: `.next` (auto)

### Substrate Web
- **Root directory**: `substrate-api/web/`
- **Framework**: Next.js (auto-detected)
- **Build command**: `npm run build` (auto)
- **Output directory**: `.next` (auto)

## Deployment Steps

### 1. Push to GitHub
```bash
git push origin main
```

### 2. Update Render Services
Go to Render Dashboard:
- **Work Platform API**: Update service name to `yarnnn-work-platform-api`, Root Directory to `work-platform/api/`
- **Substrate API**: Ensure service name is `yarnnn-substrate-api`, Root Directory is `substrate-api/api/`

### 3. Update Vercel Projects
Go to Vercel Dashboard:
- **Work Platform Web**: Update Root Directory to `work-platform/web/`
- **Substrate Web**: Ensure Root Directory is `substrate-api/web/`

## Infrastructure Layer

The `infra/` directory contains **pure utilities only** (no business logic):
- `infra/utils/` - JWT, Supabase client, database utilities
- `infra/substrate/` - Shared substrate models and types

**Important**:
- Both Work Platform and Substrate APIs import from `infra.*`
- Work Platform API uses local `app.utils.*` for work-specific code
- Substrate API uses `infra.*` for all shared utilities

## Migration History

### Phase 1: Import Fixes (Completed)
- Work Platform API no longer depends on `/shared` directory
- All imports use local copies: `app.utils.*`, `services.*`, `app.models.*`

### Phase 2: Architecture Refactor (Completed)
- Renamed `enterprise/` → `substrate-api/` (P0-P4 pipeline + memory domain)
- Renamed `platform/` → `work-platform/` (consumer/work-facing app)
- Renamed `shared/` → `infra/` (infrastructure-only utilities)
- Updated all substrate-api imports: `shared.*` → `infra.*`
- Updated render.yaml service names and paths

### Phase 3: BFF Implementation + Domain Hardening (In Progress)
**Phase 3.1 - Foundation (Completed)**:
- Created HTTP client (`work-platform/api/src/clients/substrate_client.py`) with:
  - Service token authentication
  - Retry logic with exponential backoff
  - Circuit breaker for fault tolerance
  - Connection pooling via httpx
- Added service-to-service auth middleware in Substrate API
- Created test suite (`test_bff_foundation.py`)
- Updated work-platform requirements (added tenacity for retries)

**Phase 3.2 - Domain Hardening (Current)**:
- Renamed `platform/` → `work-platform/` for clarity
- Identified agent pipeline code in work-platform (should be in substrate-api)
- Migration path: Remove or move agent code to substrate-api

**Next Steps**:
- Phase 3.3: Remove agent pipeline from work-platform
- Phase 3.4: Remove direct substrate DB access from work-platform
- Phase 3.5+: See [PHASE3_BFF_IMPLEMENTATION_PLAN.md](PHASE3_BFF_IMPLEMENTATION_PLAN.md)

## Testing Deployment

### Platform API Health Check
```bash
curl https://yarnnn-platform-api.onrender.com/health
```

### Substrate API Health Check
```bash
curl https://yarnnn-substrate-api.onrender.com/health
```

### MCP Integration Test
```bash
curl https://yarnnn-substrate-api.onrender.com/api/mcp/v1/resources
```

## Troubleshooting

### Import Errors
**Platform API:**
- Should use `app.utils.*`, `services.*`, `app.models.*`
- NO imports from `infra.*` or `shared.*`

**Substrate API:**
- Should use `infra.*` for shared utilities
- NO imports from `shared.*`

### Missing Environment Variables
Check Render/Vercel dashboard to ensure all env vars are set correctly.

### Database Connection Issues
Verify `DATABASE_URL` and `SUPABASE_URL` are correct and accessible from service.

### Render Cache Issues
If deployment shows old code:
1. Go to Render Dashboard → Service Settings
2. Manual Deploy → Clear build cache & deploy
3. Or Suspend → Resume service

## Architecture Decision Records

### Why Substrate API (not "Enterprise")?
- "Enterprise" was misleading - didn't reflect actual domain
- "Substrate" clearly indicates memory/context management
- Aligns with codebase terminology (substrate blocks, relationships, etc.)

### Why `infra/` (not "shared")?
- "Shared" implies sharing business logic (anti-pattern)
- "Infrastructure" clarifies this is utilities-only
- Forces proper domain separation

### Why BFF Pattern?
- Follows industry best practices (Anthropic Claude, OpenAI ChatGPT)
- Clear separation of product logic vs core domain
- Enables independent scaling and evolution
- Platform can evolve UX without touching substrate
