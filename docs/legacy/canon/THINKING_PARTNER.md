# Thinking Partner - Meta-Agent Documentation

**Status**: MVP Complete (Day 1-5 of 7)
**Last Updated**: 2025-11-20
**Implementation**: [thinking_partner.py](../../work-platform/api/src/agents_sdk/thinking_partner.py)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation](#implementation)
4. [API Reference](#api-reference)
5. [Testing](#testing)
6. [Future Work](#future-work)

---

## Overview

### What is Thinking Partner?

Thinking Partner (TP) is a **meta-agent** that orchestrates specialized agents (research, content, reporting) and provides intelligent assistance to users through a conversational chat interface.

**Key Capabilities**:
- Chat interface for user interaction
- Query substrate knowledge base
- Delegate work to specialized agents
- Plan multi-step workflows
- Query work orchestration state
- Emit meta-intelligence (insights, recommendations)

### Gateway/Mirror/Meta Pattern

**Gateway**: Receives all user interaction
- Single chat interface for all agent operations
- Users don't directly call specialized agents
- TP decides which agents to use and when

**Mirror**: Orchestrates YARNNN infrastructure
- Delegates to agents via `agent_orchestration` tool
- Queries work state via `infra_reader` tool
- Plans workflows via `steps_planner` tool
- Creates work_requests, work_tickets, manages execution

**Meta**: Emits own intelligence
- Pattern recognition ("I notice you...")
- Recommendations ("You should...")
- Recursion decisions (should output → substrate?)
- System-level insights

---

## Architecture

### Design Decision: Agent SDK Build

**Chosen Approach**: Build TP as agent extending BaseAgent (not custom FastAPI app)

**Why**:
- ✅ **489 lines** vs 2000 for custom app
- ✅ **0 new tables** vs 2 for custom app
- ✅ **5 days** to MVP vs 3 weeks for custom
- ✅ Reuses AgentSession, SubstrateMemoryAdapter, agent_orchestration.py
- ✅ Score: **99/100** vs 38/100 for custom approach

**What We Get For Free**:
- Conversation management (AgentSession)
- Memory queries (SubstrateMemoryAdapter)
- Session resumption (claude_session_id)
- Tool execution framework
- Error handling and logging

### Component Diagram

```
┌─────────────────────────────────────────────┐
│ THINKING PARTNER (Intelligence Layer)       │
│ - Understands user intent                   │
│ - Queries substrate + TP memory             │
│ - Decides which agents to run               │
│ - Synthesizes outputs                       │
│ - Converses with user                       │
│ - Makes recursion decisions                 │
└─────────────────────────────────────────────┘
                    ↓ delegates to
┌─────────────────────────────────────────────┐
│ SPECIALIZED AGENTS                          │
│ - ResearchAgent (deep analysis)             │
│ - ContentAgent (creative production)        │
│ - ReportingAgent (data synthesis)           │
└─────────────────────────────────────────────┘
                    ↓ query/write
┌─────────────────────────────────────────────┐
│ SUBSTRATE (Knowledge Base)                  │
│ - Blocks (facts)                            │
│ - Documents (compositions)                  │
│ - Timeline (history)                        │
│ - TP Memory (meta-intelligence)             │
└─────────────────────────────────────────────┘
```

### Database Schema Integration

**Uses Existing Tables** (ZERO new tables):

**agent_sessions** (Phase 2e):
- ONE session per (basket_id, agent_type="thinking_partner")
- Stores claude_session_id for conversation resumption
- UNIQUE constraint enforced
- Long-lived, accumulates conversation history

**work_requests** (when TP delegates):
- Created when user asks TP to do work
- TP's delegation creates work_request
- Tracks user intent

**work_tickets** (execution tracking):
- Created when TP delegates to specialized agent
- Tracks agent execution (pending → running → completed)
- Links to work_outputs

### Tools

TP has **4 tools** for orchestration:

#### 1. agent_orchestration
**Purpose**: Delegate work to specialized agents

**Agents Available**: research, content, reporting

**How It Works**:
```python
# User: "Research AI agents"
# TP calls tool:
{
  "agent_type": "research",
  "task": "Research AI agents",
  "parameters": {}
}

# Tool execution:
# 1. Delegates to agent_orchestration.py:run_agent_task()
# 2. Creates work_request, work_ticket
# 3. Executes ResearchAgent.deep_dive("Research AI agents")
# 4. Returns work_outputs to TP
# 5. TP synthesizes in response
```

#### 2. infra_reader
**Purpose**: Query work orchestration infrastructure

**Query Types**:
- `recent_work_requests` - What has user asked for?
- `work_tickets_by_status` - What's running/completed?
- `agent_sessions` - Active agent conversations
- `work_history` - Complete execution history
- `work_outputs_by_type` - Deliverables (TODO: substrate-API query)

**Use Case**: Avoid redundant work
```python
# TP checks if recent research exists before running new research
result = infra_reader({
  "query_type": "recent_work_requests",
  "filters": {"limit": 5}
})
# Returns: "Recent research on AI agents 2 days ago"
# TP: "I see we have recent research. Should I use that or run fresh?"
```

#### 3. steps_planner
**Purpose**: Plan multi-step workflows using LLM

**How It Works**:
```python
# User: "Research competitors then create LinkedIn post"
# TP calls:
{
  "user_request": "Research competitors then create LinkedIn post",
  "existing_context": "We have some competitor data from last week"
}

# Returns:
"""
Execution Plan:
Step 1: Research Phase
- Agent: research
- Task: Deep dive on competitor landscape
- Dependencies: None

Step 2: Content Creation
- Agent: content
- Task: Create LinkedIn post from research
- Dependencies: Step 1
"""
```

#### 4. emit_work_output
**Purpose**: TP emits its own intelligence

**Use Cases**:
- Pattern recognition: "I notice you reject emoji-heavy posts"
- Recommendations: "You should add Competitor X to your watchlist"
- Meta-insights: "Your content performs 3x better with data"

---

## Implementation

### Core Class

```python
from agents_sdk.thinking_partner import ThinkingPartnerAgent, create_thinking_partner

# Create TP
tp = create_thinking_partner(
    basket_id="basket_abc",
    workspace_id="ws_001",
    user_id="user_123"
)

# Chat
result = await tp.chat(
    user_message="I need LinkedIn content about AI agents"
)

# Returns:
# {
#     "message": "I see we have research from last week. Use that or fresh?",
#     "claude_session_id": "session_xyz",
#     "work_outputs": [...],  # Any outputs TP emitted
#     "actions_taken": ["Queried memory", "Checked work history"]
# }
```

### Key Methods

**chat(user_message, claude_session_id=None)**
- Primary interface for TP interaction
- Queries memory for context
- Calls Claude with tools
- Handles tool execution
- Returns synthesized response

**_execute_agent_orchestration(tool_input)**
- Delegates to specialized agents
- Creates work_request + work_ticket
- Executes agent via agent_orchestration.py
- Returns work_outputs summary

**_execute_infra_reader(tool_input)**
- Queries work-platform infrastructure
- Direct Supabase queries for work state
- Returns formatted results

**_execute_steps_planner(tool_input)**
- Plans multi-step workflows
- Uses Claude to generate execution plan
- Returns numbered steps with agent assignments

### Configuration

**BaseAgent Extension**:
```python
super().__init__(
    agent_type="thinking_partner",
    agent_name="Thinking Partner",
    memory=SubstrateMemoryAdapter(...),
    anthropic_api_key=...,
    model="claude-sonnet-4-5",
    ticket_id=work_ticket_id,
    claude_ticket_id=claude_session_id,
)

# Override Claude client (remove Skills beta headers)
self.claude = AsyncAnthropic(api_key=anthropic_api_key)
```

**Tools Registration**:
```python
self._tools = [
    self._create_agent_orchestration_tool(),
    self._create_infra_reader_tool(),
    self._create_steps_planner_tool(),
    EMIT_WORK_OUTPUT_TOOL,
]
```

---

## API Reference

### Endpoints

#### POST /api/tp/chat
Send message to Thinking Partner.

**Request**:
```json
{
  "basket_id": "basket_abc",
  "message": "I need LinkedIn content about AI agents",
  "claude_session_id": null  // or session ID to resume
}
```

**Response**:
```json
{
  "message": "I see we have research on AI agents from 3 days ago...",
  "claude_session_id": "session_xyz",
  "session_id": "agent_session_123",
  "work_outputs": [],
  "actions_taken": ["Queried memory", "Checked work history"]
}
```

#### GET /api/tp/session/{session_id}
Get session details.

**Response**:
```json
{
  "session_id": "agent_session_123",
  "claude_session_id": "session_xyz",
  "basket_id": "basket_abc",
  "workspace_id": "ws_001",
  "user_id": "user_123",
  "created_at": "2025-11-20T10:00:00Z",
  "updated_at": "2025-11-20T11:00:00Z",
  "metadata": {}
}
```

#### GET /api/tp/capabilities
Get TP capabilities and available tools.

**Response**:
```json
{
  "description": "Thinking Partner - Meta-agent that orchestrates specialized agents",
  "pattern": "Gateway/Mirror/Meta",
  "capabilities": [
    "Chat interface for user interaction",
    "Query substrate knowledge base",
    "Delegate to specialized agents",
    "Plan multi-step workflows",
    "Query work orchestration state",
    "Emit meta-intelligence"
  ],
  "tools": {
    "agent_orchestration": {...},
    "infra_reader": {...},
    "steps_planner": {...},
    "emit_work_output": {...}
  },
  "agents_available": ["research", "content", "reporting"]
}
```

---

## Testing

### Integration Tests

**File**: [test_tp_standalone.py](../../work-platform/api/test_tp_standalone.py)

**Results**: 5/6 passing (83%)

```bash
cd work-platform/api
python3 test_tp_standalone.py
```

**Tests**:
- ✅ TP initialization (tools, memory, session)
- ✅ Tool definitions (structure validation)
- ❌ Infrastructure reader (requires Supabase env vars)
- ✅ Steps planner (workflow planning)
- ✅ Basic chat (conversation)
- ✅ Gateway/Mirror/Meta pattern

### API Tests

**File**: [test_tp_api.sh](../../work-platform/api/test_tp_api.sh)

```bash
cd work-platform/api
./test_tp_api.sh
```

**Requires**: Server running on localhost:8000

**Tests**:
- GET /api/tp/capabilities (unauthenticated)
- POST /api/tp/chat (requires JWT)
- GET /api/tp/session/{id} (requires JWT)

---

## Future Work

### Phase 3: Full Features

**Multi-Turn Agentic Loop**:
- Tool use → tool result → continue reasoning
- Multiple agent delegations in single conversation
- Synthesize outputs from multiple agents

**Advanced Workflow Planning**:
- Parallel agent execution
- Conditional workflows (if X fails, try Y)
- User-configurable workflow templates

**Pattern Learning**:
- Track user preferences (content styles, platforms)
- Learn rejection patterns from work_outputs
- Suggest proactive work

**Recursion Judgment**:
- Decide: should agent output → substrate block?
- Create raw_dumps from derived intelligence
- Systemic updates ("Add to watchlist")

### Frontend (Day 6-7)

**TPChat.tsx Component**:
- Message list with markdown rendering
- Progressive disclosure of work outputs
- Inline approval workflow
- Session management
- Loading states, error handling

**Chat Interface Features**:
- 80% of interactions via chat
- Specialized views for deep review (20%)
- Inline work output cards
- Agent delegation visibility
- Workflow planning preview

---

## Related Documentation

- **Multi-Agent Orchestration**: [MULTI_AGENT_ORCHESTRATION.md](MULTI_AGENT_ORCHESTRATION.md)
- **Phase 2e Architecture**: [PHASE_2E_SESSION_ARCHITECTURE.md](PHASE_2E_SESSION_ARCHITECTURE.md)
- **Agent Substrate**: [AGENT_SUBSTRATE_ARCHITECTURE.md](AGENT_SUBSTRATE_ARCHITECTURE.md)

---

**Implementation Status**: MVP Complete ✓
**Next Phase**: Frontend Chat UI + Full Deployment
