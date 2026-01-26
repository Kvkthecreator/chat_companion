# Chat Companion Documentation

AI companion for people in transition — follows up on the things that matter.

## Documentation Index

### Strategic Analysis
- [Domain Layer Architecture](analysis/DOMAIN_LAYER_ARCHITECTURE.md) - **START HERE** - Infrastructure vs. consumer gap analysis
- [First Principles Framework](analysis/FIRST_PRINCIPLES_FRAMEWORK.md) - Axiomatic foundation
- [Product Wedge Analysis](analysis/PRODUCT_WEDGE_ANALYSIS.md) - Positioning exploration log
- [Founder Journey Synthesis](analysis/FOUNDER_JOURNEY_SYNTHESIS.md) - Product evolution history
- [Daisy Strategic Brief](analysis/DAISY_STRATEGIC_BRIEF_ANALYSIS.md) - Cross-analysis with strategic brief

### Development
- [Local Setup](development/SETUP.md) - Getting started with local development
- [Architecture](development/ARCHITECTURE.md) - System design and data flow
- [Frontend Assessment](development/FRONTEND_ARCHITECTURE_ASSESSMENT.md) - Frontend alignment with product vision

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
- [Internationalization](features/INTERNATIONALIZATION.md) - Multi-language support (parked)

### Design
- [Companion Outreach System](design/COMPANION_OUTREACH_SYSTEM.md) - Multi-trigger messaging architecture
- [Pattern Detection](design/PATTERN_DETECTION_AND_MEMORY_TRANSPARENCY.md) - Behavioral patterns and transparency
- [Notification Channel Philosophy](design/NOTIFICATION_CHANNEL_PHILOSOPHY.md) - Dedicated app model decision

### Implementation Plans
- [Domain Layer Implementation](implementation/DOMAIN_LAYER_IMPLEMENTATION.md) - **ACTIVE** - Thread templates, onboarding redesign, frontend surfacing
- [Memory Features Plan](implementation/MEMORY_FEATURES_IMPLEMENTATION_PLAN.md) - Memory system enhancements
- [Extraction Observability](implementation/EXTRACTION_OBSERVABILITY.md) - Background job monitoring

### Architecture Decisions
- [ADR Index](adr/README.md) - Architecture Decision Records

### Archive
- [Channel Simplification](archive/CHANNEL_SIMPLIFICATION_IMPLEMENTATION.md) - Implemented
- [Product Vision Gap Analysis](archive/PRODUCT_VISION_GAP_ANALYSIS.md) - Gap was fixed

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
