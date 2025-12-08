# TP Configuration Audit & Optimization Analysis - November 21, 2025

## Current Architecture Audit

### 1. **Memory Loading Pattern** (CURRENT - EVERY MESSAGE)

**Location**: [thinking_partner_sdk.py:898-903](../../work-platform/api/src/agents_sdk/thinking_partner_sdk.py#L898-L903)

```python
async def chat(self, user_message: str, claude_session_id: Optional[str] = None):
    # ...
    # Query memory for context
    context = None
    if self.memory:
        memory_results = await self.memory.query(user_message, limit=5)  # ❌ EVERY MESSAGE!
        if memory_results:
            context = "\n".join([r.content for r in memory_results])

    # Build prompt with context
    full_prompt = user_message
    if context:
        full_prompt = f"""**Relevant Context from Memory:**
{context}

**User Message:**
{user_message}"""
```

**What Happens**:
1. User sends message
2. TP calls `memory.query(user_message, limit=5)` → SubstrateMemoryAdapter
3. SubstrateMemoryAdapter calls `client.get_basket_blocks()` → substrate-API HTTP call
4. Retrieves 5 blocks from database
5. Injects blocks into prompt
6. Sends to Claude SDK

**Performance Impact**:
- ~200-500ms per substrate-API HTTP call
- Circuit breaker risk if substrate-API slow/down
- Happens EVERY single chat message (even "hello")
- Adds latency even when memory not needed

### 2. **System Prompt Architecture**

**Location**: [thinking_partner_sdk.py:51-143](../../work-platform/api/src/agents_sdk/thinking_partner_sdk.py#L51-L143)

**Key Instructions** (lines 105-127):
```
When user makes a request:
1. **Understand Intent**: What does user want?
2. **Query Context**: What do we already know? (memory.query)  ← Instruction to query!
3. **Check Work State**: Any relevant ongoing/past work? (infra_reader)
4. **Decide Action** (KEY DECISION):
   - **Quick query?** → Use specialist subagent (read-only, fast)
   - **New work needed?** → Use work_orchestration tool (creates work_request/work_ticket)
   - **Complex workflow?** → Use steps_planner, then work_orchestration
```

**Decision Matrix** (lines 123-127):
```
- User wants ANSWER from existing knowledge → Specialist subagent (fast, no work_request)
- User wants NEW DELIVERABLE (content, research, report) → work_orchestration tool (tracked, billed)
- User wants guidance/advice → Direct answer or specialist subagent
- User wants multi-step execution → steps_planner + work_orchestration
```

**Problem**: System prompt INSTRUCTS TP to query memory (line 108) as step 2, but this is baked into the code too (line 901).

### 3. **Specialist Subagents** (Lightweight, Read-Only)

**Purpose**: Fast answers from existing knowledge WITHOUT creating work_requests

**Three Specialists** (lines 150-244):

1. **research_specialist**:
   - "What do we know about X?"
   - Query memory for blocks/documents
   - Synthesize existing knowledge
   - **Does NOT**: Run web searches, create work_outputs

2. **content_specialist**:
   - "What content style works best?"
   - Review past content performance
   - Brand voice guidance
   - **Does NOT**: Create new content drafts

3. **reporting_specialist**:
   - "What metrics are important?"
   - Summarize key metrics from past reports
   - Data interpretation guidance
   - **Does NOT**: Generate new reports/files

**Key Characteristic**: All specialist subagents access memory via TP's memory adapter (inherited).

### 4. **Work Orchestration Tool** (Creates Work Requests)

**Purpose**: Delegate to specialist agents for NEW DELIVERABLES (tracked work)

**Location**: Currently disabled (lines 974-978) - needs MCP migration

**Intended Flow**:
```
User: "Create LinkedIn post about AI agents"
  ↓
TP: Calls work_orchestration(agent_type="content", task="...")
  ↓
Creates: work_request, work_ticket, agent_session (specialist)
  ↓
Specialist Agent (ContentAgentSDK): Executes with memory access
  ↓
Emits: work_outputs (deliverables)
  ↓
TP: Reviews outputs, responds to user
```

### 5. **Claude Agent SDK Session Management**

**Built-in Memory** (confirmed in SDK docs):
- Session persistence via `claude_session_id`
- Conversation history maintained by Claude
- Multi-turn context without re-loading substrate

**Current Implementation**:
```python
# Resume session (line 922-925)
if claude_session_id:
    await client.connect(session_id=claude_session_id)
else:
    await client.connect()

# Send query with context
await client.query(full_prompt)  # Includes memory context IF loaded

# Receive response
async for message in client.receive_response():
    # Process response...
```

**Key Point**: Claude SDK manages conversation history INTERNALLY. Substrate memory is ADDITIONAL context, not required for basic chat.

### 6. **Frontend Side Panel** (LiveContextPane)

**Location**: [LiveContextPane.tsx](../../work-platform/web/components/thinking/LiveContextPane.tsx)

**States** (lines 64-99):
- `idle`: Ready state
- `planning`: Multi-step workflow planning
- `delegating`: Selecting specialist agent
- `executing`: Agent running work
- `reviewing`: Analyzing work outputs
- `responding`: Formulating response

**Views** (lines 122-310):
- **IdleView**: Shows substrate overview (blocks, documents, recent work)
- **PlanningView**: Shows workflow steps being planned
- **DelegatingView**: Shows agent selection (Research/Content/Reporting)
- **ExecutingView**: Shows execution progress
- **ReviewingView**: Shows work outputs summary
- **RespondingView**: TP thinking indicator

**Key Insight**: Side panel ALREADY visualizes TP workflow states. User can see when TP is delegating vs chatting.

## Your Insights - Decoded

### Insight 1: "Substrate calling doesn't need to happen every chat message"

**✅ CORRECT**. Current implementation:
- Line 901: `memory_results = await self.memory.query(user_message, limit=5)` on EVERY message
- Even casual chat like "hello" or "thanks" triggers substrate HTTP call
- Claude SDK already has conversation history via session management

**Waste**: Substrate memory should be TOOL-BASED, not automatic.

### Insight 2: "Claude Agent SDK session management has built-in memory"

**✅ CORRECT**. Per official docs:
- Sessions persist conversation history
- Multi-turn context without re-querying
- `claude_session_id` enables resumption
- Memory is conversation history, not knowledge base

**Implication**: For casual chat, TP doesn't need substrate blocks. SDK handles "what did we talk about?"

### Insight 3: "Substrate memory should happen as part of work-request triggering"

**✅ ARCHITECTURALLY SOUND**. Your vision:

```
User: "Research AI agent frameworks"
  ↓
TP (WITHOUT substrate memory): Understands intent, decides to delegate
  ↓
TP: Calls work_orchestration(agent_type="research", task="...")
  ↓ (THIS is when substrate memory loads)
Specialist Agent (ResearchAgentSDK):
  - NOW loads substrate memory via SubstrateMemoryAdapter
  - Uses memory for context-aware research
  - Emits work_outputs
  ↓
TP: Reviews outputs, responds to user (NO memory load for TP response)
```

**Benefits**:
- No substrate call for casual chat
- Memory loaded ONLY when agent needs it (work execution)
- TP conversation relies on Claude SDK session (fast)
- Substrate memory = tool for knowledge-intensive work

### Insight 4: "TP collecting work request information via chat"

**Your Vision** (interpretation):

**Scenario**: User wants content but TP needs more info

```
User: "I need a LinkedIn post"
  ↓
TP (chat-based): "Great! What topic? Target audience?"
  ↓ (NO substrate memory load yet - just chat)
User: "About AI agents, for technical audience"
  ↓
TP (chat-based): "Got it. Should I use recent research on agents?"
  ↓ (STILL no substrate - just conversation via SDK session)
User: "Yes, use the competitor analysis from last week"
  ↓
TP: NOW triggers work_orchestration
  ↓ (Substrate memory loads for ContentAgent, not TP)
ContentAgent: Executes with full substrate context
```

**Pattern**: Multi-turn chat to COLLECT requirements, THEN delegate with full context.

### Insight 5: "Side panel for work request details outside chat"

**Your Vision** (interpretation):

**Two Input Modes**:

1. **Chat Mode** (current):
   - User types naturally in chat
   - TP asks clarifying questions
   - When ready, TP triggers work

2. **Form Mode** (future enhancement):
   - Side panel shows "Work Request Builder" form
   - Fields: Agent Type, Task Description, Priority, etc.
   - User fills form explicitly
   - TP receives structured input, delegates immediately

**UI Pattern**:
```
┌─────────────────┬──────────────────────────┐
│  Chat (40%)     │  LiveContextPane (60%)   │
│                 │                          │
│  User: "I need  │  ┌────────────────────┐  │
│  research"      │  │ Work Request Form  │  │
│                 │  │                    │  │
│  TP: "What      │  │ Agent: [Research]  │  │
│  topic?"        │  │ Task:  ___________  │  │
│                 │  │ Priority: [Medium]  │  │
│  OR click       │  │                    │  │
│  form →         │  │ [Submit]           │  │
│                 │  └────────────────────┘  │
└─────────────────┴──────────────────────────┘
```

**Benefits**:
- Explicit work request creation (no ambiguity)
- TP can pre-fill form based on chat context
- User can review/edit before submission
- Clean separation: chat vs. work creation

## Current Problems - Summary

### Problem 1: Memory Loaded Too Eagerly
- **Current**: Every message → substrate HTTP call
- **Should Be**: Only when agent needs knowledge context (work execution)

### Problem 2: TP System Prompt Duplicates Code
- **Current**: System prompt says "query memory" + code auto-queries
- **Should Be**: System prompt describes memory as TOOL, not automatic step

### Problem 3: Work Orchestration Disabled
- **Current**: Custom tools (work_orchestration) commented out (line 974-978)
- **Should Be**: Migrated to MCP servers, properly enabled

### Problem 4: No Structured Work Request UI
- **Current**: All work requests via natural language chat
- **Could Be**: Side panel form for explicit work creation

### Problem 5: Specialist Subagents Also Query Memory
- **Current**: Subagents inherit TP's memory adapter → substrate calls
- **Question**: Should specialist subagents query substrate, or just use SDK session?

## Optimization Opportunities

### Optimization 1: Memory as Tool (Not Automatic)

**Change**: Make substrate memory a TOOL that TP can CHOOSE to use.

**Implementation**:
1. Remove automatic memory query (line 901)
2. Create `query_substrate` MCP tool
3. System prompt instructs TP: "Use query_substrate tool when you need knowledge base context"
4. TP decides: "User asking about past research" → calls tool → gets memory

**Benefits**:
- No substrate call for "hello", "thanks", "what can you do?"
- TP decides when memory needed (contextual intelligence)
- Faster responses for simple chat

### Optimization 2: Memory-on-Delegation Pattern

**Change**: Load substrate memory ONLY when delegating to specialist agents.

**Implementation**:
1. TP chat: No substrate memory (relies on Claude SDK session)
2. TP delegates: `work_orchestration(agent_type="research", ...)`
3. Specialist agent: Receives SubstrateMemoryAdapter with user_token
4. Specialist agent: Queries substrate when executing (line 901 in specialist SDK)

**Benefits**:
- TP is fast (no substrate calls)
- Specialists get full context (substrate memory when needed)
- Clean separation: conversation vs. knowledge work

### Optimization 3: Lazy Memory Loading with Caching

**Change**: Load substrate memory once per session, cache it.

**Implementation**:
```python
class ThinkingPartnerAgentSDK:
    def __init__(self, ...):
        self._memory_cache = None  # Cache blocks for session
        self._memory_loaded = False

    async def _load_memory_if_needed(self):
        """Load substrate memory once per session."""
        if not self._memory_loaded:
            self._memory_cache = await self.memory.query("", limit=50)  # Load all
            self._memory_loaded = True
            logger.info(f"Loaded {len(self._memory_cache)} blocks (cached for session)")
        return self._memory_cache

    async def chat(self, user_message, ...):
        # Option A: Load on first message only
        if not self._memory_loaded:
            await self._load_memory_if_needed()

        # Option B: Load when TP decides it's needed (via tool)
        # Don't load automatically
```

**Benefits**:
- Single HTTP call per session (amortized cost)
- Subsequent messages use cache (instant)
- Trade-off: Stale memory if substrate updates during session

### Optimization 4: Structured Work Request Form UI

**Frontend Enhancement**:

Add to LiveContextPane:
```tsx
{tpPhase === 'collecting_requirements' && (
  <WorkRequestFormView
    onSubmit={(workRequest) => {
      // Send structured work request to TP
      gateway.createWorkRequest(workRequest);
    }}
  />
)}
```

**Backend Enhancement**:
```python
@router.post("/tp/work-request", response_model=TPChatResponse)
async def create_work_request(
    request: WorkRequestCreate,  # Structured input
    user: dict = Depends(verify_jwt)
):
    """
    Create work request explicitly (bypasses chat collection).

    TP receives structured input:
    - agent_type: "research" | "content" | "reporting"
    - task: str
    - priority: "high" | "medium" | "low"
    - context_hints: List[str]  # User-selected blocks
    """
    # TP immediately delegates (no chat collection phase)
    # ...
```

**Benefits**:
- User control (explicit work creation)
- No ambiguity (structured input)
- TP can pre-fill based on chat history
- Side panel shows form when appropriate

## Recommended Architecture Changes

### Phase 1: Memory as Tool (Immediate Impact)

**Goal**: Stop automatic memory loading on every message.

**Changes**:
1. Remove line 901: `memory_results = await self.memory.query(...)`
2. Create `query_substrate_memory` MCP tool
3. Update system prompt:
   - OLD: "2. **Query Context**: What do we already know? (memory.query)"
   - NEW: "2. **Query Context (if needed)**: Use query_substrate_memory tool when user asks about past work or knowledge"
4. TP decides when to call tool

**Impact**:
- ✅ Casual chat: No substrate calls → faster responses
- ✅ Knowledge queries: TP calls tool → gets memory
- ✅ Work delegation: Specialist agents still get memory
- ✅ Backward compatible: Memory still available via tool

### Phase 2: Memory-on-Delegation Pattern (Architectural Shift)

**Goal**: Load substrate memory ONLY during work execution, not TP chat.

**Changes**:
1. Remove SubstrateMemoryAdapter from TP initialization (line 291)
2. TP chat: Pure conversation via Claude SDK session (no substrate)
3. Specialist agents: Receive SubstrateMemoryAdapter on delegation
4. Work orchestration: Pass user_token to specialist SDK constructors

**Implementation**:
```python
# TP SDK - NO memory adapter
class ThinkingPartnerAgentSDK:
    def __init__(self, ...):
        # self.memory = SubstrateMemoryAdapter(...)  # REMOVED
        self.memory = None  # No memory for TP chat

# Work orchestration - pass memory to specialist
async def _execute_work_orchestration(self, tool_input):
    agent_type = tool_input['agent_type']
    task = tool_input['task']

    # Create memory adapter for specialist
    specialist_memory = SubstrateMemoryAdapter(
        basket_id=self.basket_id,
        workspace_id=self.workspace_id,
        user_token=self.user_token,
        agent_type=agent_type
    )

    # Create specialist with memory
    if agent_type == "research":
        agent = ResearchAgentSDK(
            session=specialist_session,
            memory=specialist_memory  # Specialist gets memory
        )
```

**Impact**:
- ✅ TP chat: Zero substrate calls → very fast
- ✅ Specialists: Full substrate context when executing
- ✅ Clear ownership: TP = conversation, Specialists = knowledge work
- ⚠️ Breaking change: TP can't answer "what do we know about X?" without tool

### Phase 3: Hybrid Model (Best of Both Worlds)

**Goal**: TP has memory via TOOL, specialists have memory automatically.

**Architecture**:
```
TP Chat:
  - Pure conversation (Claude SDK session)
  - Can call query_substrate_memory TOOL when needed
  - No automatic memory loading

Specialist Execution (via work_orchestration):
  - Receives SubstrateMemoryAdapter
  - Automatically loads memory on execution
  - Full substrate context for work
```

**Benefits**:
- ✅ Fast TP chat (no automatic loading)
- ✅ TP can still access memory (via tool, on-demand)
- ✅ Specialists always have context (automatic for work)
- ✅ User control: Chat naturally or use form for explicit work

## Questions for Clarification

1. **Memory Access Pattern**:
   - Should TP have memory access at all (via tool)?
   - Or should TP ONLY delegate to specialists for knowledge queries?

2. **Specialist Subagents**:
   - Should specialist subagents (research_specialist, content_specialist, reporting_specialist) query substrate?
   - Or should they rely purely on Claude SDK session (lightweight)?

3. **Work Request Collection**:
   - Prefer natural language chat collection (current)?
   - Or add structured form UI in side panel?
   - Or both (user choice)?

4. **Memory Caching Strategy**:
   - Load once per session and cache?
   - Or always fetch fresh (no cache, but slower)?
   - Or lazy load on first tool call?

5. **Side Panel Integration**:
   - Should side panel show work request form?
   - Should it show real-time work progress?
   - Should it show substrate query results?

## Next Steps

Based on your priorities, I recommend:

1. **Start with Phase 1** (Memory as Tool):
   - Quick win, immediate performance improvement
   - Low risk, backward compatible
   - Can iterate based on usage patterns

2. **Frontend Enhancement** (Work Request Form):
   - Add structured form UI in LiveContextPane
   - User choice: chat collection vs. explicit form
   - Complements Phase 1 (structured input)

3. **Monitor Usage** (Analytics):
   - How often does TP need substrate memory?
   - How often do users ask knowledge queries vs. create work?
   - Inform Phase 2 decision (memory-on-delegation)

4. **Migrate Work Orchestration** (Enable Tools):
   - Create MCP servers for custom tools
   - Enable work_orchestration, infra_reader, steps_planner
   - Validate end-to-end flow

**Let me know**:
- Which optimization approach resonates?
- Any clarifications needed on current architecture?
- Should I proceed with Phase 1 implementation (memory as tool)?
