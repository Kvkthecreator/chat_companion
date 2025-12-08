# Baskets System Workflow Documentation

## 📋 Executive Summary

The Baskets system is a full-stack intelligence platform that transforms raw user inputs into structured knowledge through a sophisticated agent orchestration pipeline. This document provides a comprehensive overview of the entire workflow, from initial content capture to final document generation.

## 🏗️ System Architecture Overview

```
User Input → Raw Dumps → Substrate Processing → Manager Agent → Structured Output
     ↓           ↓              ↓                  ↓             ↓
Frontend     API Proxy     Agent Orchestra    Delta System   Document View
```

## 🔄 Complete Workflow

### 1. Content Ingestion (`/web/app/api/dumps/new/route.ts`)

**Entry Point**: User creates raw content via memory capture, file upload, or direct input

**Processing Flow**:
- Authentication verification via Supabase auth
- Workspace validation and access control
- Field mapping for compatibility (`body_md` → `text_dump`, `file_refs` → `file_urls`)
- Dual-path processing:
  - **Primary**: External backend API call to `rightnow-api.onrender.com`
  - **Fallback**: Local Supabase storage with substrate processing trigger

**Key Features**:
- Filename sanitization for special characters (fixed Korean filename issue)
- CORS handling for cross-origin requests
- 15-second timeout protection
- Automatic substrate processing initiation

### 2. Substrate Processing (`/web/app/api/substrate/process/route.ts`)

**Purpose**: Transform raw content into structured knowledge components

**Agent Orchestra**:
1. **Block Proposer Agent (P1)**: Extracts structured knowledge ingredients (goals, constraints, metrics, entities) from content
2. **Context Extractor Agent (P1)**: Identifies themes, questions, and key concepts with semantic classification
3. **Narrative Builder Agent (P4)**: Composes coherent documents from structured ingredients
4. **Relationship Mapper Agent (P2)**: Maps connections between substrate elements

**Output Structure**:
- **Blocks**: Structured knowledge ingredients containing:
  - Goals: Objectives and desired outcomes
  - Constraints: Limitations and requirements  
  - Metrics: Measurable criteria and success indicators
  - Entities: Key actors, systems, and components
  - Provenance: Source text spans for traceability
  - Confidence scores and semantic types
- **Context Items**: Themes, questions, and significant concepts with semantic classification
- **Narrative Elements**: Documents composed from substrate ingredients
- **Relationships**: Substrate interconnections and dependencies

**Database Integration**:
- Atomic transactions ensure data consistency
- Graceful degradation for missing table schemas
- Comprehensive metadata tracking for audit trails

### 3. Manager Agent Integration (`/web/app/api/baskets/[id]/work/route.ts`)

**Role**: API bridge between frontend and external manager agent

**Functionality**:
- Proxies requests to external backend manager agent
- Handles manager agent responses and delta generation
- Provides fallback mechanisms for system resilience
- Maintains session continuity across agent interactions

### 4. User Review & Feedback System

**Block Lifecycle Management**:
- **Accept**: `/web/app/api/blocks/[id]/accept/route.ts`
- **Reject**: `/web/app/api/blocks/[id]/reject/route.ts`

**Features**:
- Workspace-scoped access control
- Audit trail with user attribution
- Event logging for analytics
- Status state management (proposed → accepted/rejected)

**Delta Tracking**: `/web/app/api/baskets/[id]/deltas/route.ts`
- Real-time change monitoring
- External backend integration with local fallback
- CORS-enabled for frontend consumption

## 🎯 User Interface Flow

### Baskets Overview (`/web/app/baskets/page.tsx`)
- Basket listing with search and sort capabilities
- Authentication-gated access
- Pagination for large datasets
- Direct integration with `getAllBaskets` service

### Basket Work Environment (`/web/app/baskets/[id]/work/layout.tsx`)
- Three-panel layout: WorkLeft, Center Content, WorkRight
- Focus context management for user attention
- Real-time basket state synchronization

### Dashboard Metrics (`/web/components/features/basket/centers/DashboardCenter.tsx`)
- Memory density as primary metric (structured thoughts)
- Secondary metrics: captures, documents
- Recent activity feed with delta summaries
- Graceful error handling with retry mechanisms

## 🔧 Data Flow Architecture

### Authentication & Authorization
1. Supabase auth verification on all API endpoints
2. Workspace-scoped access control
3. Real workspace ID usage (fixed from hardcoded "default")

### State Management
- **BasketContext**: Provides basket state across components
- **Real-time Events**: `useBasketEvents` for live updates
- **Query Integration**: `useBasket`, `useBasketDeltas` hooks

### Error Handling
- **File Upload**: Sanitized filenames prevent Supabase Storage errors
- **Schema Compatibility**: API routes handle missing database columns
- **Network Resilience**: Fallback mechanisms for external service failures
- **User Experience**: Graceful degradation with informative error states

## 🚀 Key Technical Achievements

### Recent Fixes Applied
1. **Filename Sanitization**: Resolved Korean character upload issues
2. **Schema Alignment**: Fixed database column mismatches
3. **Workspace Integration**: Real workspace IDs throughout the system
4. **Build Compatibility**: TypeScript errors resolved for deployment

### Performance Optimizations
- **Atomic Database Transactions**: Ensures data consistency
- **Intelligent Fallbacks**: Maintains system availability
- **Memory Density Focus**: Single primary metric reduces cognitive load
- **Lazy Loading**: Components load progressively for better UX

## ⚠️ Identified Gaps & Recommendations

### High Priority
1. **External Backend Dependency**: System relies heavily on `rightnow-api.onrender.com`
   - **Risk**: Single point of failure
   - **Recommendation**: Implement robust local processing capabilities

2. **Database Schema Evolution**: Some tables (context_items, narrative) may not exist
   - **Risk**: Feature degradation in new environments
   - **Recommendation**: Database migration strategy and schema validation

### Medium Priority
3. **Agent Response Validation**: Limited validation of external agent responses
   - **Risk**: Malformed data could break UI components
   - **Recommendation**: Response schema validation and sanitization

4. **Real-time Synchronization**: Delta updates rely on polling rather than websockets
   - **Risk**: Delayed updates and increased server load
   - **Recommendation**: WebSocket implementation for real-time updates

### Low Priority
5. **Mock Data Strategies**: Development fallbacks could be more sophisticated
   - **Recommendation**: Improved development experience with realistic mock data

## 🎯 Next Steps

1. **Strengthen Local Processing**: Reduce external backend dependencies
2. **Implement Schema Validation**: Ensure database compatibility across environments
3. **Add Response Validation**: Protect against malformed agent responses
4. **Real-time Updates**: WebSocket integration for live collaboration
5. **Enhanced Monitoring**: Comprehensive logging and analytics integration

---

*This documentation reflects the current state of the Baskets system as of 2025-08-12. The system demonstrates a sophisticated approach to knowledge management with intelligent agent orchestration and user-centric design.*