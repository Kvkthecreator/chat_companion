# Chat Companion Documentation

Push-based AI companion that reaches out daily via Telegram, WhatsApp, or Web.

## Documentation Index

### Development
- [Local Setup](development/SETUP.md) - Getting started with local development
- [Architecture](development/ARCHITECTURE.md) - System design and data flow

### API
- [Endpoints](api/ENDPOINTS.md) - Complete API reference
- [Authentication](api/AUTHENTICATION.md) - JWT and auth flow

### Database
- [Schema](database/SCHEMA.md) - Table definitions and SQL
- [Data Model](database/DATA_MODEL.md) - Design decisions and relationships
- [Access](database/ACCESS.md) - Connection strings and direct access

### Deployment
- [Render (API)](deployment/RENDER.md) - Backend deployment
- [Vercel (Web)](deployment/VERCEL.md) - Frontend deployment

### Operations
- [Troubleshooting](operations/TROUBLESHOOTING.md) - Common issues and solutions
- [Monitoring](operations/MONITORING.md) - Logs and health checks

### Features
- [Memory System](features/MEMORY_SYSTEM.md) - Context extraction and retrieval
- [Personalization](features/PERSONALIZATION.md) - User preferences and adaptation
- [Scheduler](features/SCHEDULER.md) - Daily message scheduling
- [Telegram Integration](features/TELEGRAM.md) - Bot setup and webhook

### Architecture Decisions
- [ADR Index](adr/README.md) - Architecture Decision Records

---

## Quick Start

1. **Local Development**: Start with [development/SETUP.md](development/SETUP.md)
2. **Deploy**: Follow [deployment/RENDER.md](deployment/RENDER.md) and [deployment/VERCEL.md](deployment/VERCEL.md)
3. **Troubleshoot**: Check [operations/TROUBLESHOOTING.md](operations/TROUBLESHOOTING.md)

## Documentation Standards

- **ADRs** for significant architectural decisions
- **Feature docs** explain the "why" not just the "how"
- Keep docs close to the code they describe
- Update docs when code changes
