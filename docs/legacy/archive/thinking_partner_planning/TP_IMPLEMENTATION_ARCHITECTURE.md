# Thinking Partner Implementation Architecture

**Date**: 2025-11-20
**Context**: Detailed implementation design for TP MVP to get the details right
**Goal**: De-risk implementation complexity with concrete architecture decisions

---

## Executive Summary

**The Core Concern**: "Will we get the implementation details right?"

**The Answer**: YES - if we make the right architectural decisions upfront and learn from existing patterns.

**Strategy**:
1. Start with **simple, proven patterns** (rule-based → LLM-based)
2. Reuse **existing infrastructure** (don't rebuild)
3. Make **critical design decisions** explicit (document trade-offs)
4. Build **incrementally** (validate each layer)

---

## Part 1: Critical Design Decisions (Make These First)

### Decision 1: Where Does TP Live?

**Options**:

**A) TP in substrate-API** (from original docs)
```
substrate-API database:
  ├─ blocks, documents, insights
  ├─ thinking_partner_memory
  └─ thinking_partner_chats

work-platform:
  ├─ Makes API calls to substrate-API for TP
  └─ No TP logic in work-platform
```

**Pros**:
- ✅ TP memory colocated with substrate (no cross-DB joins)
- ✅ Clean separation (TP is knowledge layer)
- ✅ Matches original architecture docs

**Cons**:
- ❌ substrate-API doesn't have agent execution logic
- ❌ TP needs to orchestrate agents (work-platform's job)
- ❌ Creates circular dependency (substrate-API ↔ work-platform)

---

**B) TP in work-platform** (recommended)
```
work-platform:
  ├─ Thinking Partner logic
  ├─ Agent orchestration
  ├─ TP chats (local table)
  └─ Queries substrate-API for context

work-platform database:
  ├─ work_requests, work_tickets, work_outputs
  ├─ thinking_partner_chats (NEW)
  └─ thinking_partner_memory (NEW)

substrate-API:
  ├─ blocks, documents (queried by TP)
  └─ No TP logic
```

**Pros**:
- ✅ TP next to agent orchestration (natural fit)
- ✅ TP can reuse agent_orchestration.py
- ✅ No circular dependency
- ✅ TP has access to work state (work_requests, work_tickets)

**Cons**:
- ⚠️ TP memory not colocated with substrate
- ⚠️ Need cross-DB queries for TP memory + substrate

**Trade-off Analysis**:
- TP's PRIMARY job is **orchestration** (work-platform domain)
- TP's SECONDARY job is **context synthesis** (queries substrate)
- **Conclusion**: TP belongs in work-platform

---

**RECOMMENDATION**: **TP in work-platform**

**Rationale**:
1. TP orchestrates agents → needs access to agent execution
2. agent_orchestration.py already exists in work-platform
3. TP needs work state (work_requests, work_tickets) → in work-platform DB
4. TP can query substrate via BFF (existing pattern)

**Migration path** (if needed later):
- If TP memory grows large → migrate to substrate-API
- Keep TP execution logic in work-platform
- Separate storage from logic

---

### Decision 2: How Does TP Parse Intent?

**Options**:

**A) Rule-based (MVP approach)**
```python
class IntentParser:
    def parse(self, user_msg: str) -> Intent:
        msg_lower = user_msg.lower()

        # Simple keyword matching
        if "research" in msg_lower:
            return Intent(action="research", topic=self.extract_topic(user_msg))
        elif any(platform in msg_lower for platform in ["linkedin", "twitter", "blog"]):
            return Intent(action="content", platform=self.extract_platform(user_msg))
        elif "report" in msg_lower or "analyze" in msg_lower:
            return Intent(action="reporting", topic=self.extract_topic(user_msg))
        else:
            # Default: Research
            return Intent(action="research", topic=user_msg)
```

**Pros**:
- ✅ Simple, fast, predictable
- ✅ No LLM cost for parsing
- ✅ Easy to debug
- ✅ Works for 80% of cases

**Cons**:
- ❌ Brittle (keyword-based)
- ❌ Doesn't handle complex queries
- ❌ No understanding of nuance

**Example**:
- ✅ "Research competitor pricing" → Works
- ✅ "Create LinkedIn post about AI" → Works
- ❌ "Help me understand our market position" → Fails (ambiguous)

---

**B) LLM-based (structured output)**
```python
class IntentParser:
    async def parse(self, user_msg: str) -> Intent:
        response = await self.claude.messages.create(
            model="claude-haiku-20250305",  # Fast, cheap
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Parse this user request into structured intent:

User request: "{user_msg}"

Return JSON:
{{
  "action": "research" | "content" | "reporting" | "chat",
  "topic": "extracted topic",
  "platform": "linkedin" | "twitter" | "blog" | null,
  "parameters": {{...}}
}}"""
            }]
        )

        return Intent.from_json(response.content[0].text)
```

**Pros**:
- ✅ Handles complex queries
- ✅ Understands nuance
- ✅ Flexible (adapts to new patterns)

**Cons**:
- ❌ LLM cost per parse (~$0.0001)
- ❌ Latency (~200ms)
- ❌ Non-deterministic

**Example**:
- ✅ "Research competitor pricing" → Works
- ✅ "Help me understand our market position" → Works (maps to research)
- ✅ "What's our current pricing?" → Works (maps to chat)

---

**RECOMMENDATION**: **Start rule-based, migrate to LLM**

**Phase 3a MVP**: Rule-based (simple, fast)
**Phase 3b+**: LLM-based (when complexity increases)

**Hybrid approach** (best of both):
```python
class IntentParser:
    async def parse(self, user_msg: str) -> Intent:
        # Try rule-based first (fast)
        intent = self.try_rule_based(user_msg)

        if intent.confidence > 0.8:
            return intent  # Clear match, no LLM needed
        else:
            # Ambiguous, use LLM
            return await self.parse_with_llm(user_msg)
```

**Cost**: Only pay for LLM when needed (20-30% of queries)

---

### Decision 3: How Does TP Decide Which Agents to Run?

**Options**:

**A) Static decision tree (MVP)**
```python
class AgentSelector:
    def select(self, intent: Intent) -> List[str]:
        if intent.action == "research":
            return ["research"]

        elif intent.action == "content":
            # Check if we need research first
            if self.has_fresh_research(intent.topic, days=7):
                return ["content"]  # Skip research
            else:
                return ["research", "content"]  # Research first

        elif intent.action == "reporting":
            return ["reporting"]

        else:
            return ["research"]  # Default
```

**Pros**:
- ✅ Simple, predictable
- ✅ Easy to debug
- ✅ No LLM cost

**Cons**:
- ❌ Rigid (can't adapt)
- ❌ New patterns require code changes

---

**B) LLM-based planner**
```python
class AgentSelector:
    async def select(self, intent: Intent, context: Dict) -> List[str]:
        # Query substrate for relevant context
        substrate_knowledge = await self.query_substrate(intent.topic)
        work_history = await self.query_work_history(intent.topic)

        # Ask LLM to plan
        response = await self.claude.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""You are a work orchestration planner.

User intent: {intent}

Available agents:
- research: Deep analysis, multi-source synthesis
- content: Platform-optimized content creation
- reporting: Data visualization and reports

Current context:
- Substrate knowledge: {substrate_knowledge}
- Recent work: {work_history}

Decide which agents to run and in what order.
Return JSON:
{{
  "plan": ["agent1", "agent2"],
  "reasoning": "why this sequence"
}}"""
            }]
        )

        plan = json.loads(response.content[0].text)
        return plan["plan"]
```

**Pros**:
- ✅ Flexible, adaptive
- ✅ Context-aware decisions
- ✅ Handles novel cases

**Cons**:
- ❌ LLM cost per decision (~$0.001)
- ❌ Latency (~1-2 seconds)
- ❌ Less predictable

---

**RECOMMENDATION**: **Static decision tree for MVP, with LLM escape hatch**

```python
class AgentSelector:
    async def select(self, intent: Intent) -> List[str]:
        # Try static rules first
        plan = self.try_static_rules(intent)

        if plan:
            return plan  # Clear case, use rules
        else:
            # Complex case, use LLM planner
            return await self.plan_with_llm(intent)
```

**Rationale**: 90% of cases follow patterns (use rules), 10% need intelligence (use LLM)

---

### Decision 4: How Does TP Synthesize Multi-Agent Outputs?

**Scenario**: User asked for content, TP ran research + content agents

**Options**:

**A) Simple concatenation (MVP)**
```python
class OutputSynthesizer:
    def synthesize(self, outputs: List[AgentResult]) -> str:
        response = []

        for result in outputs:
            response.append(f"**{result.agent_type} Results**:")
            for output in result.work_outputs:
                response.append(f"- {output.title}")

        return "\n".join(response)
```

**Output**:
```
**research Results**:
- Finding: Competitor pricing trends
- Insight: 3x engagement with data-driven posts

**content Results**:
- LinkedIn post about AI agents
```

**Pros**:
- ✅ Simple, fast
- ✅ All outputs visible

**Cons**:
- ❌ Not conversational
- ❌ No synthesis/narrative

---

**B) LLM-based synthesis**
```python
class OutputSynthesizer:
    async def synthesize(self, outputs: List[AgentResult], intent: Intent) -> str:
        # Collect all outputs
        all_outputs = []
        for result in outputs:
            all_outputs.extend(result.work_outputs)

        # Ask LLM to synthesize
        response = await self.claude.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""You are synthesizing results from multiple AI agents.

User's original request: {intent.original_message}

Agent outputs:
{json.dumps(all_outputs, indent=2)}

Create a conversational response that:
1. Answers the user's request
2. Highlights key findings
3. Cites which agent produced each insight
4. Suggests next steps if appropriate

Be concise and natural."""
            }]
        )

        return response.content[0].text
```

**Output**:
```
I've created your LinkedIn post about AI agents. Here's what I found:

The research agent discovered that data-driven posts get 3x higher
engagement (based on recent competitor analysis). I used this insight
to create a stat-heavy post that highlights 5 key AI agent trends.

The post is ready for your review. Would you like me to adjust the
tone or add more data points?
```

**Pros**:
- ✅ Conversational, natural
- ✅ Intelligent synthesis
- ✅ Better UX

**Cons**:
- ❌ LLM cost (~$0.002)
- ❌ Latency (~2-3 seconds)

---

**RECOMMENDATION**: **LLM synthesis (worth the cost)**

**Rationale**: This is the UX differentiator - natural conversation vs raw outputs

**Cost**: ~$0.002 per synthesis (acceptable for value delivered)

---

### Decision 5: How Does TP Store and Query Memory?

**Schema** (in work-platform DB):

```sql
-- Thinking Partner Memory
CREATE TABLE thinking_partner_memory (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  basket_id uuid NOT NULL REFERENCES baskets(id),
  user_id uuid REFERENCES auth.users(id),  -- NULL = basket-level

  -- Memory type
  memory_type text NOT NULL CHECK (memory_type IN (
    'user_preference',  -- "User prefers data-driven posts"
    'pattern',          -- "Research on weekends gets rejected"
    'insight',          -- "Competitor X is aggressive"
    'system'            -- "Research agent config updated"
  )),

  -- Content
  content jsonb NOT NULL,
  -- Example:
  -- {
  --   "pattern": "User prefers data-driven content",
  --   "confidence": 0.85,
  --   "evidence": ["work_output_123", "work_output_456"],
  --   "sample_size": 15
  -- }

  -- Provenance
  derived_from_work_outputs uuid[],
  derived_from_chats uuid[],

  -- Lifecycle
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  expires_at timestamptz,  -- Some patterns expire

  -- Validation
  confidence numeric CHECK (confidence BETWEEN 0 AND 1),
  user_validated boolean DEFAULT null,
  validated_at timestamptz
);

CREATE INDEX idx_tp_memory_basket ON thinking_partner_memory(basket_id);
CREATE INDEX idx_tp_memory_type ON thinking_partner_memory(memory_type);
CREATE INDEX idx_tp_memory_confidence ON thinking_partner_memory(confidence DESC);

-- Thinking Partner Chats
CREATE TABLE thinking_partner_chats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  basket_id uuid NOT NULL REFERENCES baskets(id),
  user_id uuid NOT NULL REFERENCES auth.users(id),

  -- Thread management
  thread_id uuid DEFAULT gen_random_uuid(),

  -- Message
  role text NOT NULL CHECK (role IN ('user', 'assistant')),
  content text NOT NULL,

  -- Context used (for provenance)
  context_queried jsonb,
  -- {
  --   "substrate_blocks": ["block_123", "block_456"],
  --   "work_outputs": ["output_789"],
  --   "tp_memory": ["memory_012"]
  -- }

  -- Agent actions (if TP triggered agents)
  triggered_agents text[],  -- ["research", "content"]
  work_request_ids uuid[],  -- References to work_requests

  -- Timestamps
  created_at timestamptz DEFAULT now()
);

CREATE INDEX idx_tp_chats_basket ON thinking_partner_chats(basket_id);
CREATE INDEX idx_tp_chats_thread ON thinking_partner_chats(thread_id, created_at);
CREATE INDEX idx_tp_chats_user ON thinking_partner_chats(user_id, created_at DESC);
```

**Querying Strategy**:

```python
class ThinkingPartnerMemory:
    async def query_relevant_memory(
        self,
        basket_id: str,
        user_id: str,
        intent: Intent
    ) -> List[Memory]:
        """
        Query TP memory relevant to current intent.
        """

        # 1. User preferences (always relevant)
        user_prefs = await self.db.query(
            "SELECT * FROM thinking_partner_memory "
            "WHERE basket_id = $1 AND user_id = $2 "
            "AND memory_type = 'user_preference' "
            "AND confidence > 0.7 "
            "ORDER BY confidence DESC LIMIT 5",
            basket_id, user_id
        )

        # 2. Topic-specific patterns
        topic_patterns = await self.db.query(
            "SELECT * FROM thinking_partner_memory "
            "WHERE basket_id = $1 "
            "AND memory_type = 'pattern' "
            "AND content->>'topic' = $2 "  # JSONB query
            "AND confidence > 0.6 "
            "ORDER BY confidence DESC LIMIT 5",
            basket_id, intent.topic
        )

        # 3. Recent insights
        recent_insights = await self.db.query(
            "SELECT * FROM thinking_partner_memory "
            "WHERE basket_id = $1 "
            "AND memory_type = 'insight' "
            "AND created_at > now() - interval '30 days' "
            "ORDER BY created_at DESC LIMIT 5",
            basket_id
        )

        return user_prefs + topic_patterns + recent_insights
```

**Learning Strategy** (how TP builds memory):

```python
class ThinkingPartnerLearning:
    async def learn_from_approval(
        self,
        work_output_id: str,
        approved: bool,
        user_feedback: Optional[str]
    ):
        """
        Learn patterns from user approval/rejection.
        """

        # Get work output details
        output = await self.get_work_output(work_output_id)

        # Extract pattern
        if output.output_type == "content" and not approved:
            # User rejected content - why?
            if "emoji" in output.body:
                await self.update_or_create_memory({
                    "memory_type": "user_preference",
                    "content": {
                        "pattern": "User dislikes emoji-heavy content",
                        "confidence": 0.7,
                        "evidence": [work_output_id]
                    }
                })

        elif output.output_type == "finding" and approved:
            # User approved research - good quality signal
            if output.confidence > 0.8:
                await self.update_or_create_memory({
                    "memory_type": "pattern",
                    "content": {
                        "pattern": f"High-confidence research on {output.topic} is valuable",
                        "confidence": 0.75,
                        "evidence": [work_output_id]
                    }
                })
```

---

### Decision 6: How Does TP Handle Multi-Turn Conversations?

**Challenge**: User asks follow-up questions

**Example**:
```
User: "Create LinkedIn post about AI agents"
TP: [orchestrates research + content] "Here's your post..."

User: "Make it more data-driven"
TP: [needs to understand context - what post? what data?]
```

**Solution**: Thread-based context management

```python
class ThinkingPartner:
    async def handle_message(
        self,
        user_msg: str,
        thread_id: Optional[str] = None
    ) -> TPResponse:

        # 1. Get or create thread
        if not thread_id:
            thread_id = str(uuid4())

        # 2. Get conversation history
        history = await self.get_chat_history(thread_id, limit=10)

        # 3. Build context for LLM
        context_messages = []
        for msg in history:
            context_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # Add current message
        context_messages.append({
            "role": "user",
            "content": user_msg
        })

        # 4. Parse intent WITH conversation context
        intent = await self.parse_intent_with_context(
            current_message=user_msg,
            conversation_history=history
        )

        # 5. Check if this is a follow-up
        if self.is_follow_up(intent, history):
            # Reference previous work
            previous_work = self.get_recent_work_from_thread(thread_id)
            return await self.handle_follow_up(
                intent,
                previous_work
            )
        else:
            # New request
            return await self.handle_new_request(intent)
```

**Key pattern**: Thread maintains context, TP uses history to understand follow-ups

---

## Part 2: TP MVP Implementation Plan

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User Interface (web/apps/web or separate)                   │
│ - Chat input                                                 │
│ - Conversation thread display                                │
│ - Work output review                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│ Thinking Partner API (work-platform/api/src/app/tp/)        │
│                                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ThinkingPartner (main orchestrator)                      │ │
│ │ - handle_message()                                        │ │
│ │ - handle_follow_up()                                      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│ │ IntentParser │  │ MemoryQuery  │  │ AgentSelector    │   │
│ │ (rule-based) │  │ (TP memory)  │  │ (decision tree)  │   │
│ └──────────────┘  └──────────────┘  └──────────────────┘   │
│                            ↓                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ AgentOrchestrator (reuses agent_orchestration.py)       │ │
│ │ - delegate_to_agent()                                    │ │
│ │ - wait_for_completion()                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                            ↓                                 │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│ │ ResearchSDK  │  │ ContentSDK   │  │ ReportingSDK     │   │
│ │ (existing)   │  │ (existing)   │  │ (existing)       │   │
│ └──────────────┘  └──────────────┘  └──────────────────┘   │
│                            ↓                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ OutputSynthesizer (LLM-based)                            │ │
│ │ - synthesize_response()                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Data Layer                                                   │
│                                                               │
│ work-platform DB:                substrate-API:              │
│ - thinking_partner_chats          - blocks (queried)         │
│ - thinking_partner_memory         - documents (queried)      │
│ - work_requests                   - insights (queried)       │
│ - work_tickets                                               │
│ - work_outputs                                               │
└─────────────────────────────────────────────────────────────┘
```

---

### File Structure

```
work-platform/api/src/app/
├─ tp/                              ← NEW: Thinking Partner module
│   ├─ __init__.py
│   ├─ thinking_partner.py          ← Main TP class
│   ├─ intent_parser.py             ← Intent parsing logic
│   ├─ memory_manager.py            ← TP memory queries
│   ├─ agent_selector.py            ← Agent decision logic
│   ├─ output_synthesizer.py        ← Multi-agent synthesis
│   └─ models.py                    ← TP data models (Intent, Memory, etc.)
│
├─ routes/
│   ├─ agent_orchestration.py      ← EXISTS (reused by TP)
│   └─ tp_routes.py                 ← NEW: TP HTTP endpoints
│
└─ services/
    └─ work_output_service.py       ← EXISTS (reused by TP)
```

---

### Core Classes

#### 1. ThinkingPartner (Main Orchestrator)

```python
# work-platform/api/src/app/tp/thinking_partner.py

from typing import Dict, Any, Optional, List
from uuid import UUID, uuid4
import logging

from .intent_parser import IntentParser
from .memory_manager import MemoryManager
from .agent_selector import AgentSelector
from .output_synthesizer import OutputSynthesizer
from .models import Intent, TPResponse, ChatMessage

from app.routes.agent_orchestration import _run_research_agent, _run_content_agent, _run_reporting_agent
from adapters.memory_adapter import SubstrateMemoryAdapter

logger = logging.getLogger(__name__)


class ThinkingPartner:
    """
    Thinking Partner - Intelligence layer for YARNNN.

    Responsibilities:
    - Parse user intent from natural language
    - Query substrate + TP memory for context
    - Decide which agents to run
    - Orchestrate agent execution
    - Synthesize multi-agent outputs
    - Learn from user feedback
    """

    def __init__(
        self,
        basket_id: str,
        workspace_id: str,
        user_id: str,
        anthropic_api_key: str
    ):
        self.basket_id = basket_id
        self.workspace_id = workspace_id
        self.user_id = user_id

        # Components
        self.intent_parser = IntentParser()
        self.memory_manager = MemoryManager(basket_id, user_id)
        self.agent_selector = AgentSelector(basket_id, workspace_id)
        self.output_synthesizer = OutputSynthesizer(anthropic_api_key)

        # Substrate access
        self.substrate_memory = SubstrateMemoryAdapter(
            basket_id=basket_id,
            workspace_id=workspace_id
        )

    async def handle_message(
        self,
        user_message: str,
        thread_id: Optional[str] = None
    ) -> TPResponse:
        """
        Main entry point for TP interactions.

        Args:
            user_message: User's natural language message
            thread_id: Optional conversation thread ID

        Returns:
            TPResponse with synthesized answer and actions taken
        """

        # 1. Thread management
        if not thread_id:
            thread_id = str(uuid4())

        logger.info(f"TP handling message in thread {thread_id}: {user_message[:100]}")

        # 2. Get conversation history
        conversation_history = await self.memory_manager.get_chat_history(
            thread_id,
            limit=10
        )

        # 3. Parse intent (with conversation context)
        intent = await self.intent_parser.parse(
            user_message=user_message,
            conversation_history=conversation_history
        )

        logger.info(f"Parsed intent: action={intent.action}, topic={intent.topic}")

        # 4. Query context
        context = await self._gather_context(intent)

        # 5. Decide if this is a follow-up or new request
        if self._is_follow_up(intent, conversation_history):
            response = await self._handle_follow_up(
                intent,
                context,
                conversation_history
            )
        else:
            response = await self._handle_new_request(
                intent,
                context
            )

        # 6. Store chat history
        await self._store_chat_turn(
            thread_id=thread_id,
            user_message=user_message,
            assistant_response=response.message,
            context_used=context,
            agents_triggered=response.agents_triggered
        )

        # 7. Learn from this interaction (async)
        # TODO: Background task for learning

        return response

    async def _gather_context(self, intent: Intent) -> Dict[str, Any]:
        """
        Gather all relevant context for decision-making.

        Returns:
            Dictionary with substrate knowledge, TP memory, work history
        """

        # Query substrate
        substrate_results = []
        if intent.topic:
            substrate_results = await self.substrate_memory.query(
                intent.topic,
                limit=5
            )

        # Query TP memory
        tp_memory = await self.memory_manager.query_relevant_memory(
            intent
        )

        # Query recent work history
        work_history = await self.memory_manager.get_recent_work(
            topic=intent.topic,
            days=7
        )

        return {
            "substrate_knowledge": [
                {"content": r.content, "block_id": r.metadata.get("block_id")}
                for r in substrate_results
            ],
            "tp_memory": tp_memory,
            "work_history": work_history
        }

    def _is_follow_up(
        self,
        intent: Intent,
        conversation_history: List[ChatMessage]
    ) -> bool:
        """
        Determine if this is a follow-up to previous message.

        Simple heuristic: If last message was from TP and less than 5 min ago
        """

        if not conversation_history:
            return False

        last_message = conversation_history[-1]
        if last_message.role != "assistant":
            return False

        # Check recency (5 minutes)
        import datetime
        time_diff = datetime.datetime.now() - last_message.created_at
        if time_diff.total_seconds() > 300:  # 5 minutes
            return False

        return True

    async def _handle_new_request(
        self,
        intent: Intent,
        context: Dict[str, Any]
    ) -> TPResponse:
        """
        Handle new user request (not a follow-up).

        Steps:
        1. Decide which agents to run
        2. Execute agents
        3. Synthesize outputs
        """

        # 1. Decide which agents
        agent_plan = await self.agent_selector.select(intent, context)

        logger.info(f"Agent plan: {agent_plan}")

        # 2. Execute agents
        agent_outputs = []
        work_request_ids = []

        for agent_type in agent_plan:
            output = await self._execute_agent(agent_type, intent)
            agent_outputs.append(output)
            if output.get("work_request_id"):
                work_request_ids.append(output["work_request_id"])

        # 3. Synthesize
        synthesized_message = await self.output_synthesizer.synthesize(
            agent_outputs=agent_outputs,
            original_intent=intent,
            context=context
        )

        return TPResponse(
            message=synthesized_message,
            agents_triggered=agent_plan,
            work_request_ids=work_request_ids,
            context_used=context
        )

    async def _handle_follow_up(
        self,
        intent: Intent,
        context: Dict[str, Any],
        conversation_history: List[ChatMessage]
    ) -> TPResponse:
        """
        Handle follow-up question/request.

        For MVP: Simple approach - answer from context without triggering agents
        """

        # Get previous work from conversation
        previous_work = self._extract_previous_work(conversation_history)

        # For MVP: Just return conversational response
        # TODO: More sophisticated follow-up handling

        message = f"Based on our previous conversation about {intent.topic}, ..."

        return TPResponse(
            message=message,
            agents_triggered=[],
            work_request_ids=[],
            context_used=context
        )

    async def _execute_agent(
        self,
        agent_type: str,
        intent: Intent
    ) -> Dict[str, Any]:
        """
        Execute a single agent.

        Delegates to existing agent_orchestration.py functions.
        """

        # Build agent request
        from app.routes.agent_orchestration import AgentTaskRequest

        request = AgentTaskRequest(
            agent_type=agent_type,
            task_type=self._map_intent_to_task_type(agent_type, intent),
            basket_id=self.basket_id,
            parameters=intent.parameters
        )

        # Create work ticket
        work_ticket_id = await self._create_work_ticket_for_tp(
            agent_type,
            intent
        )

        # Execute via existing functions
        if agent_type == "research":
            result = await _run_research_agent(
                request,
                self.user_id,
                work_ticket_id
            )
        elif agent_type == "content":
            result = await _run_content_agent(
                request,
                self.user_id,
                work_ticket_id
            )
        elif agent_type == "reporting":
            result = await _run_reporting_agent(
                request,
                self.user_id,
                work_ticket_id
            )
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        return result

    def _map_intent_to_task_type(
        self,
        agent_type: str,
        intent: Intent
    ) -> str:
        """Map intent to agent-specific task type."""

        if agent_type == "research":
            return "deep_dive"
        elif agent_type == "content":
            return "create"
        elif agent_type == "reporting":
            return "generate"
        else:
            return "execute"

    async def _store_chat_turn(
        self,
        thread_id: str,
        user_message: str,
        assistant_response: str,
        context_used: Dict,
        agents_triggered: List[str]
    ):
        """Store chat turn in database."""

        # TODO: Implement database storage
        pass

    def _extract_previous_work(
        self,
        conversation_history: List[ChatMessage]
    ) -> List[Dict]:
        """Extract work outputs from previous messages."""

        # TODO: Implement
        return []

    async def _create_work_ticket_for_tp(
        self,
        agent_type: str,
        intent: Intent
    ) -> str:
        """Create work ticket for TP-triggered agent execution."""

        # TODO: Reuse _create_work_ticket from agent_orchestration.py
        pass
```

---

#### 2. IntentParser (Rule-Based MVP)

```python
# work-platform/api/src/app/tp/intent_parser.py

from typing import List, Optional
from .models import Intent, ChatMessage
import re


class IntentParser:
    """
    Parse user messages into structured intent.

    MVP: Rule-based keyword matching
    Future: LLM-based parsing
    """

    PLATFORM_KEYWORDS = {
        "linkedin": ["linkedin", "li"],
        "twitter": ["twitter", "tweet", "thread"],
        "blog": ["blog", "article", "post"],
        "instagram": ["instagram", "ig", "insta"]
    }

    ACTION_KEYWORDS = {
        "research": ["research", "analyze", "investigate", "study", "explore"],
        "content": ["create", "write", "draft", "generate", "make"],
        "reporting": ["report", "dashboard", "metrics", "analytics"],
        "chat": ["what", "how", "why", "explain", "tell me", "show me"]
    }

    async def parse(
        self,
        user_message: str,
        conversation_history: Optional[List[ChatMessage]] = None
    ) -> Intent:
        """
        Parse user message into intent.

        Returns:
            Intent object with action, topic, platform, parameters
        """

        msg_lower = user_message.lower()

        # Detect action
        action = self._detect_action(msg_lower)

        # Detect platform (if content action)
        platform = None
        if action == "content":
            platform = self._detect_platform(msg_lower)

        # Extract topic
        topic = self._extract_topic(user_message)

        # Extract parameters
        parameters = {
            "topic": topic,
            "platform": platform
        }

        return Intent(
            action=action,
            topic=topic,
            platform=platform,
            parameters=parameters,
            original_message=user_message,
            confidence=0.8  # Rule-based has medium confidence
        )

    def _detect_action(self, msg_lower: str) -> str:
        """Detect primary action from message."""

        # Check each action type
        for action, keywords in self.ACTION_KEYWORDS.items():
            if any(kw in msg_lower for kw in keywords):
                # Special case: "create report" is reporting, not content
                if action == "content" and "report" in msg_lower:
                    continue
                return action

        # Default: research
        return "research"

    def _detect_platform(self, msg_lower: str) -> Optional[str]:
        """Detect platform from message."""

        for platform, keywords in self.PLATFORM_KEYWORDS.items():
            if any(kw in msg_lower for kw in keywords):
                return platform

        return None

    def _extract_topic(self, message: str) -> str:
        """
        Extract topic from message.

        Simple approach: Remove action keywords, return remainder
        """

        # Remove common action phrases
        cleaned = message
        remove_phrases = [
            "create", "write", "draft", "generate", "make",
            "research", "analyze", "investigate",
            "about", "on", "for", "regarding",
            "linkedin post", "twitter thread", "blog article"
        ]

        for phrase in remove_phrases:
            cleaned = re.sub(
                r'\b' + phrase + r'\b',
                '',
                cleaned,
                flags=re.IGNORECASE
            )

        # Clean up whitespace
        topic = ' '.join(cleaned.split())

        return topic if topic else message
```

---

---

#### 3. AgentSelector (Decision Tree with Context)

```python
# work-platform/api/src/app/tp/agent_selector.py

from typing import List, Dict, Any
from .models import Intent
import logging

logger = logging.getLogger(__name__)


class AgentSelector:
    """
    Decide which agents to run based on intent and context.

    MVP: Static decision tree
    Future: LLM-based planner
    """

    def __init__(self, basket_id: str, workspace_id: str):
        self.basket_id = basket_id
        self.workspace_id = workspace_id

    async def select(
        self,
        intent: Intent,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Select which agents to run based on intent and context.

        Args:
            intent: Parsed user intent
            context: Available context (substrate, TP memory, work history)

        Returns:
            List of agent types to run in order
        """

        # Decision tree based on intent action
        if intent.action == "research":
            return self._plan_research(intent, context)

        elif intent.action == "content":
            return self._plan_content(intent, context)

        elif intent.action == "reporting":
            return self._plan_reporting(intent, context)

        elif intent.action == "chat":
            # Chat doesn't trigger agents (TP answers from context)
            return []

        else:
            # Default: research
            return ["research"]

    def _plan_research(
        self,
        intent: Intent,
        context: Dict[str, Any]
    ) -> List[str]:
        """Plan for research intent."""

        # Always run research agent for research requests
        return ["research"]

    def _plan_content(
        self,
        intent: Intent,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Plan for content creation intent.

        Decision: Do we need research first?
        """

        # Check if we have fresh research on this topic
        has_fresh_research = self._has_fresh_research(
            intent.topic,
            context,
            days=7
        )

        if has_fresh_research:
            logger.info(f"Fresh research found for {intent.topic}, skipping research agent")
            return ["content"]
        else:
            logger.info(f"No fresh research for {intent.topic}, running research first")
            return ["research", "content"]

    def _plan_reporting(
        self,
        intent: Intent,
        context: Dict[str, Any]
    ) -> List[str]:
        """Plan for reporting intent."""

        # Always run reporting agent
        return ["reporting"]

    def _has_fresh_research(
        self,
        topic: str,
        context: Dict[str, Any],
        days: int = 7
    ) -> bool:
        """
        Check if we have fresh research on topic.

        Checks:
        1. work_history for recent research outputs
        2. substrate_knowledge for relevant blocks
        """

        import datetime

        # Check work history
        work_history = context.get("work_history", [])
        for work in work_history:
            if work.get("output_type") == "finding":
                # Check if about this topic
                if topic.lower() in work.get("title", "").lower():
                    # Check recency
                    created_at = work.get("created_at")
                    if created_at:
                        age = datetime.datetime.now() - created_at
                        if age.days < days:
                            return True

        # Check substrate knowledge
        substrate_knowledge = context.get("substrate_knowledge", [])
        if len(substrate_knowledge) >= 3:
            # Have substantial knowledge
            return True

        return False


# Future: LLM-based planner (Phase 3b+)
class LLMAgentPlanner:
    """
    LLM-based agent planning for complex cases.

    Use when static decision tree doesn't fit.
    """

    async def plan(
        self,
        intent: Intent,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Use LLM to decide which agents to run.

        TODO: Implement in Phase 3b+
        """

        # Ask Claude to plan based on intent + context
        # Return agent sequence
        pass
```

---

#### 4. MemoryManager (TP Memory & Work History)

```python
# work-platform/api/src/app/tp/memory_manager.py

from typing import List, Dict, Any, Optional
from uuid import UUID
import datetime
import logging

from .models import Intent, ChatMessage, Memory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manage TP memory and conversation history.

    Responsibilities:
    - Query TP memory for relevant patterns/preferences
    - Store and retrieve chat history
    - Query work history
    - Learn patterns from user feedback
    """

    def __init__(self, basket_id: str, user_id: str):
        self.basket_id = basket_id
        self.user_id = user_id
        # TODO: Initialize database connection
        self.db = None

    async def query_relevant_memory(
        self,
        intent: Intent
    ) -> List[Memory]:
        """
        Query TP memory relevant to current intent.

        Returns:
            List of Memory objects (preferences, patterns, insights)
        """

        memories = []

        # 1. User preferences (always relevant)
        user_prefs = await self._query_user_preferences()
        memories.extend(user_prefs)

        # 2. Topic-specific patterns
        if intent.topic:
            topic_patterns = await self._query_topic_patterns(intent.topic)
            memories.extend(topic_patterns)

        # 3. Recent insights
        recent_insights = await self._query_recent_insights(days=30)
        memories.extend(recent_insights)

        return memories

    async def _query_user_preferences(self) -> List[Memory]:
        """Query user preferences from TP memory."""

        # TODO: Implement database query
        # SELECT * FROM thinking_partner_memory
        # WHERE basket_id = $1 AND user_id = $2
        # AND memory_type = 'user_preference'
        # AND confidence > 0.7
        # ORDER BY confidence DESC LIMIT 5

        return []

    async def _query_topic_patterns(self, topic: str) -> List[Memory]:
        """Query patterns related to specific topic."""

        # TODO: Implement database query
        # SELECT * FROM thinking_partner_memory
        # WHERE basket_id = $1
        # AND memory_type = 'pattern'
        # AND content->>'topic' = $2
        # AND confidence > 0.6
        # ORDER BY confidence DESC LIMIT 5

        return []

    async def _query_recent_insights(self, days: int = 30) -> List[Memory]:
        """Query recent insights from TP memory."""

        # TODO: Implement database query
        # SELECT * FROM thinking_partner_memory
        # WHERE basket_id = $1
        # AND memory_type = 'insight'
        # AND created_at > now() - interval '30 days'
        # ORDER BY created_at DESC LIMIT 5

        return []

    async def get_chat_history(
        self,
        thread_id: str,
        limit: int = 10
    ) -> List[ChatMessage]:
        """
        Get conversation history for a thread.

        Returns:
            List of ChatMessage objects (user + assistant messages)
        """

        # TODO: Implement database query
        # SELECT * FROM thinking_partner_chats
        # WHERE thread_id = $1
        # ORDER BY created_at ASC
        # LIMIT $2

        return []

    async def get_recent_work(
        self,
        topic: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Query recent work outputs.

        Args:
            topic: Optional topic filter
            days: How many days back to look

        Returns:
            List of work_outputs
        """

        # TODO: Implement database query
        # SELECT * FROM work_outputs
        # WHERE basket_id = $1
        # AND created_at > now() - interval '7 days'
        # AND (title ILIKE '%topic%' OR content ILIKE '%topic%')
        # ORDER BY created_at DESC

        return []

    async def store_chat_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        context_queried: Optional[Dict] = None,
        triggered_agents: Optional[List[str]] = None,
        work_request_ids: Optional[List[str]] = None
    ):
        """Store a chat message in database."""

        # TODO: Implement database insert
        # INSERT INTO thinking_partner_chats (
        #   basket_id, user_id, thread_id, role, content,
        #   context_queried, triggered_agents, work_request_ids
        # ) VALUES (...)

        pass

    async def learn_from_approval(
        self,
        work_output_id: str,
        approved: bool,
        user_feedback: Optional[str] = None
    ):
        """
        Learn patterns from user approval/rejection.

        This is where TP builds intelligence over time.
        """

        # Get work output details
        output = await self._get_work_output(work_output_id)

        if not output:
            return

        # Extract patterns based on approval/rejection
        if output["output_type"] == "content" and not approved:
            # User rejected content - learn what they don't like
            await self._learn_content_rejection_pattern(output, user_feedback)

        elif output["output_type"] == "finding" and approved:
            # User approved research - learn what good research looks like
            await self._learn_research_approval_pattern(output)

    async def _learn_content_rejection_pattern(
        self,
        output: Dict,
        feedback: Optional[str]
    ):
        """Learn from rejected content."""

        # Simple pattern detection
        body = output.get("body", "")

        # Check for emojis
        if any(char in body for char in "😀🎉✨🔥"):
            await self._update_or_create_memory({
                "memory_type": "user_preference",
                "content": {
                    "pattern": "User dislikes emoji-heavy content",
                    "confidence": 0.7,
                    "evidence": [output["id"]],
                    "sample_size": 1
                }
            })

        # Check for length
        if len(body) < 100:
            await self._update_or_create_memory({
                "memory_type": "user_preference",
                "content": {
                    "pattern": "User prefers longer-form content",
                    "confidence": 0.6,
                    "evidence": [output["id"]],
                    "sample_size": 1
                }
            })

        # If feedback provided, extract more nuanced patterns
        # TODO: Use LLM to analyze feedback

    async def _learn_research_approval_pattern(self, output: Dict):
        """Learn from approved research."""

        confidence = output.get("confidence", 0)

        if confidence > 0.8:
            await self._update_or_create_memory({
                "memory_type": "pattern",
                "content": {
                    "pattern": f"High-confidence research on {output.get('topic')} is valuable",
                    "confidence": 0.75,
                    "evidence": [output["id"]],
                    "sample_size": 1
                }
            })

    async def _update_or_create_memory(self, memory_data: Dict):
        """Update existing memory or create new one."""

        # TODO: Implement upsert logic
        # 1. Check if similar memory exists
        # 2. If exists: Update confidence, add evidence, increment sample_size
        # 3. If not: Create new memory

        pass

    async def _get_work_output(self, work_output_id: str) -> Optional[Dict]:
        """Get work output by ID."""

        # TODO: Implement database query
        # SELECT * FROM work_outputs WHERE id = $1

        return None
```

---

#### 5. OutputSynthesizer (LLM-Based Multi-Agent Synthesis)

```python
# work-platform/api/src/app/tp/output_synthesizer.py

from typing import List, Dict, Any
import json
import logging
from anthropic import Anthropic

from .models import Intent

logger = logging.getLogger(__name__)


class OutputSynthesizer:
    """
    Synthesize outputs from multiple agents into conversational response.

    Uses LLM to create natural, contextual responses.
    """

    def __init__(self, anthropic_api_key: str):
        self.client = Anthropic(api_key=anthropic_api_key)

    async def synthesize(
        self,
        agent_outputs: List[Dict[str, Any]],
        original_intent: Intent,
        context: Dict[str, Any]
    ) -> str:
        """
        Synthesize multi-agent outputs into conversational response.

        Args:
            agent_outputs: Results from each agent (work_outputs + metadata)
            original_intent: User's original intent
            context: Context used for decision-making

        Returns:
            Conversational response string
        """

        # Collect all work_outputs
        all_outputs = []
        for agent_result in agent_outputs:
            outputs = agent_result.get("work_outputs", [])
            agent_type = agent_result.get("agent_type")

            for output in outputs:
                all_outputs.append({
                    "agent": agent_type,
                    "type": output.get("output_type"),
                    "title": output.get("title"),
                    "content": output.get("body", output.get("content", "")),
                    "confidence": output.get("confidence")
                })

        # Build synthesis prompt
        prompt = self._build_synthesis_prompt(
            original_intent=original_intent,
            outputs=all_outputs,
            context=context
        )

        # Call Claude for synthesis
        logger.info("Synthesizing outputs with LLM")

        response = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        synthesized = response.content[0].text

        logger.info(f"Synthesis complete ({len(synthesized)} chars)")

        return synthesized

    def _build_synthesis_prompt(
        self,
        original_intent: Intent,
        outputs: List[Dict],
        context: Dict[str, Any]
    ) -> str:
        """Build synthesis prompt for Claude."""

        prompt = f"""You are synthesizing results from multiple AI agents for a user.

**User's Original Request**: "{original_intent.original_message}"

**Intent Parsed**:
- Action: {original_intent.action}
- Topic: {original_intent.topic}
- Platform: {original_intent.platform or "N/A"}

**Agent Outputs**:
{json.dumps(outputs, indent=2)}

**Context Used**:
- Substrate knowledge: {len(context.get("substrate_knowledge", []))} blocks
- TP memory: {len(context.get("tp_memory", []))} patterns
- Work history: {len(context.get("work_history", []))} recent outputs

**Your Task**:
Create a conversational response that:

1. **Directly answers the user's request** - Don't just list outputs, provide value
2. **Highlights key findings** - What are the most important insights?
3. **Cites sources** - Which agent discovered what? (e.g., "The research agent found...")
4. **Provides actionable next steps** - What should the user do with this?
5. **Is natural and concise** - Sound like a helpful colleague, not a robot

**Tone**: Professional but conversational, helpful, insightful

**Format**: Plain text response (no markdown headers, but can use bullet points for clarity)

Generate the response:"""

        return prompt
```

---

#### 6. Data Models

```python
# work-platform/api/src/app/tp/models.py

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


@dataclass
class Intent:
    """Parsed user intent."""

    action: str  # research, content, reporting, chat
    topic: str
    platform: Optional[str] = None
    parameters: Dict[str, Any] = None
    original_message: str = ""
    confidence: float = 0.8

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class ChatMessage:
    """Single chat message in conversation."""

    id: str
    thread_id: str
    role: str  # user or assistant
    content: str
    created_at: datetime
    context_queried: Optional[Dict] = None
    triggered_agents: Optional[List[str]] = None
    work_request_ids: Optional[List[str]] = None


@dataclass
class Memory:
    """TP memory entry."""

    id: str
    basket_id: str
    user_id: Optional[str]
    memory_type: str  # user_preference, pattern, insight, system
    content: Dict[str, Any]
    confidence: float
    derived_from_work_outputs: List[str] = None
    derived_from_chats: List[str] = None
    created_at: datetime = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.derived_from_work_outputs is None:
            self.derived_from_work_outputs = []
        if self.derived_from_chats is None:
            self.derived_from_chats = []


@dataclass
class TPResponse:
    """Response from Thinking Partner."""

    message: str  # Synthesized conversational response
    agents_triggered: List[str]  # Which agents were run
    work_request_ids: List[str] = None
    context_used: Dict[str, Any] = None
    thread_id: Optional[str] = None

    def __post_init__(self):
        if self.work_request_ids is None:
            self.work_request_ids = []
        if self.context_used is None:
            self.context_used = {}
```

---

#### 7. API Routes

```python
# work-platform/api/src/app/routes/tp_routes.py

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from app.tp.thinking_partner import ThinkingPartner
from app.tp.models import TPResponse
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tp", tags=["thinking-partner"])


# Request/Response models
class TPMessageRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    basket_id: str
    workspace_id: str


class TPMessageResponse(BaseModel):
    response: str
    agents_triggered: List[str]
    work_request_ids: List[str]
    thread_id: str


class TPThreadHistoryResponse(BaseModel):
    thread_id: str
    messages: List[Dict[str, Any]]


@router.post("/message", response_model=TPMessageResponse)
async def handle_tp_message(
    request: TPMessageRequest = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    Handle a message to Thinking Partner.

    TP will:
    1. Parse intent
    2. Gather context
    3. Decide which agents to run
    4. Execute agents
    5. Synthesize response
    """

    try:
        # Initialize TP
        tp = ThinkingPartner(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id,
            user_id=user["id"],
            anthropic_api_key=user.get("anthropic_api_key")  # TODO: Get from config
        )

        # Handle message
        result = await tp.handle_message(
            user_message=request.message,
            thread_id=request.thread_id
        )

        return TPMessageResponse(
            response=result.message,
            agents_triggered=result.agents_triggered,
            work_request_ids=result.work_request_ids,
            thread_id=result.thread_id or request.thread_id
        )

    except Exception as e:
        logger.error(f"Error handling TP message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thread/{thread_id}", response_model=TPThreadHistoryResponse)
async def get_thread_history(
    thread_id: str,
    basket_id: str,
    user: dict = Depends(get_current_user)
):
    """Get conversation history for a thread."""

    try:
        # TODO: Query thinking_partner_chats
        # SELECT * FROM thinking_partner_chats
        # WHERE thread_id = $1 AND basket_id = $2
        # ORDER BY created_at ASC

        return TPThreadHistoryResponse(
            thread_id=thread_id,
            messages=[]
        )

    except Exception as e:
        logger.error(f"Error fetching thread history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def provide_feedback(
    work_output_id: str = Body(...),
    approved: bool = Body(...),
    feedback: Optional[str] = Body(None),
    basket_id: str = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    Provide feedback on work output.

    TP learns from this feedback to improve future recommendations.
    """

    try:
        # TODO: Store feedback and trigger learning
        from app.tp.memory_manager import MemoryManager

        memory = MemoryManager(basket_id, user["id"])
        await memory.learn_from_approval(
            work_output_id=work_output_id,
            approved=approved,
            user_feedback=feedback
        )

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Part 3: Database Migration

```sql
-- work-platform/api/supabase/migrations/20251120_thinking_partner_tables.sql

-- Thinking Partner Memory
CREATE TABLE thinking_partner_memory (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  basket_id uuid NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,  -- NULL = basket-level

  -- Memory type
  memory_type text NOT NULL CHECK (memory_type IN (
    'user_preference',  -- "User prefers data-driven posts"
    'pattern',          -- "Research on weekends gets rejected"
    'insight',          -- "Competitor X is aggressive"
    'system'            -- "Research agent config updated"
  )),

  -- Content (flexible JSONB)
  content jsonb NOT NULL,
  -- Example structure:
  -- {
  --   "pattern": "User prefers data-driven content",
  --   "confidence": 0.85,
  --   "evidence": ["work_output_123", "work_output_456"],
  --   "sample_size": 15,
  --   "topic": "AI agents",  -- Optional
  --   "metadata": {...}       -- Optional
  -- }

  -- Provenance
  derived_from_work_outputs uuid[],
  derived_from_chats uuid[],

  -- Lifecycle
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  expires_at timestamptz,  -- Some patterns expire (e.g., seasonal trends)

  -- Validation
  confidence numeric CHECK (confidence BETWEEN 0 AND 1),
  user_validated boolean DEFAULT null,  -- NULL = not validated, true/false = user confirmed/rejected
  validated_at timestamptz
);

-- Indexes for efficient querying
CREATE INDEX idx_tp_memory_basket ON thinking_partner_memory(basket_id);
CREATE INDEX idx_tp_memory_user ON thinking_partner_memory(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_tp_memory_type ON thinking_partner_memory(memory_type);
CREATE INDEX idx_tp_memory_confidence ON thinking_partner_memory(confidence DESC);
CREATE INDEX idx_tp_memory_created ON thinking_partner_memory(created_at DESC);
CREATE INDEX idx_tp_memory_topic ON thinking_partner_memory USING gin ((content->'topic'));

-- RLS policies
ALTER TABLE thinking_partner_memory ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view TP memory for their baskets"
  ON thinking_partner_memory FOR SELECT
  USING (
    basket_id IN (
      SELECT basket_id FROM basket_permissions
      WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Service role can manage TP memory"
  ON thinking_partner_memory
  USING (auth.role() = 'service_role');

---

-- Thinking Partner Chats
CREATE TABLE thinking_partner_chats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  basket_id uuid NOT NULL REFERENCES baskets(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Thread management (groups messages in conversation)
  thread_id uuid DEFAULT gen_random_uuid(),

  -- Message
  role text NOT NULL CHECK (role IN ('user', 'assistant')),
  content text NOT NULL,

  -- Context used (for provenance and debugging)
  context_queried jsonb,
  -- {
  --   "substrate_blocks": ["block_123", "block_456"],
  --   "work_outputs": ["output_789"],
  --   "tp_memory": ["memory_012"],
  --   "work_history": [...]
  -- }

  -- Agent actions (if TP triggered agents)
  triggered_agents text[],  -- ["research", "content"]
  work_request_ids uuid[],  -- References to work_requests created

  -- Timestamps
  created_at timestamptz DEFAULT now()
);

-- Indexes
CREATE INDEX idx_tp_chats_basket ON thinking_partner_chats(basket_id);
CREATE INDEX idx_tp_chats_user ON thinking_partner_chats(user_id, created_at DESC);
CREATE INDEX idx_tp_chats_thread ON thinking_partner_chats(thread_id, created_at ASC);
CREATE INDEX idx_tp_chats_created ON thinking_partner_chats(created_at DESC);

-- RLS policies
ALTER TABLE thinking_partner_chats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own TP chats"
  ON thinking_partner_chats FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own TP chats"
  ON thinking_partner_chats FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Service role can manage TP chats"
  ON thinking_partner_chats
  USING (auth.role() = 'service_role');

---

-- Function: Auto-update updated_at on TP memory
CREATE OR REPLACE FUNCTION update_tp_memory_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tp_memory_updated_at
  BEFORE UPDATE ON thinking_partner_memory
  FOR EACH ROW
  EXECUTE FUNCTION update_tp_memory_updated_at();
```

---

## Part 4: Integration with Existing Infrastructure

### 4.1 Reusing agent_orchestration.py

**Current**: `agent_orchestration.py` has functions like `_run_research_agent()`, `_run_content_agent()`

**TP Integration**:
```python
# In thinking_partner.py

from app.routes.agent_orchestration import (
    _run_research_agent,
    _run_content_agent,
    _run_reporting_agent,
    _create_work_ticket,
    _update_work_ticket_status
)

class ThinkingPartner:
    async def _execute_agent(self, agent_type: str, intent: Intent):
        # Create work ticket
        work_ticket_id = await _create_work_ticket(
            basket_id=self.basket_id,
            workspace_id=self.workspace_id,
            agent_type=agent_type,
            task_type=self._map_intent_to_task_type(agent_type, intent),
            parameters=intent.parameters
        )

        # Execute via existing functions
        if agent_type == "research":
            result = await _run_research_agent(...)
        # ... etc
```

**No duplication** - TP delegates to existing agent execution logic

---

### 4.2 Registering TP Routes

```python
# work-platform/api/src/app/main.py

from app.routes import tp_routes

app.include_router(tp_routes.router)
```

---

### 4.3 Frontend Integration (Minimal UI for MVP)

**New UI Component**: TP Chat Interface

```tsx
// web/apps/web/src/components/tp/TPChat.tsx

export function TPChat({ basketId, workspaceId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);

  const sendMessage = async () => {
    const response = await fetch("/api/tp/message", {
      method: "POST",
      body: JSON.stringify({
        message: input,
        thread_id: threadId,
        basket_id: basketId,
        workspace_id: workspaceId
      })
    });

    const result = await response.json();

    // Add user message
    setMessages([...messages, { role: "user", content: input }]);

    // Add TP response
    setMessages([...messages, { role: "assistant", content: result.response }]);

    setThreadId(result.thread_id);
    setInput("");
  };

  return (
    <div className="tp-chat">
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
      </div>

      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask Thinking Partner..."
        onKeyPress={(e) => e.key === "Enter" && sendMessage()}
      />
    </div>
  );
}
```

---

## Part 5: Implementation Checklist

### Phase 3a: TP Core (3 weeks)

**Week 1: Foundation**
- [ ] Create database migration (thinking_partner_chats, thinking_partner_memory)
- [ ] Implement data models (Intent, Memory, ChatMessage, TPResponse)
- [ ] Implement IntentParser (rule-based)
- [ ] Write unit tests for IntentParser

**Week 2: Orchestration**
- [ ] Implement AgentSelector (static decision tree)
- [ ] Implement OutputSynthesizer (LLM-based)
- [ ] Implement ThinkingPartner main class
- [ ] Integration with agent_orchestration.py
- [ ] Write integration tests

**Week 3: API & UI**
- [ ] Implement tp_routes.py (HTTP endpoints)
- [ ] Implement MemoryManager (chat history storage)
- [ ] Build minimal UI (TPChat component)
- [ ] End-to-end testing
- [ ] Deploy to staging

---

### Phase 3b: TP Memory (2 weeks)

**Week 1: Learning**
- [ ] Implement pattern learning from approvals/rejections
- [ ] Implement memory querying (preferences, patterns, insights)
- [ ] Build memory update/upsert logic
- [ ] Write tests for learning pipeline

**Week 2: Context-Aware Decisions**
- [ ] Enhance AgentSelector with memory context
- [ ] Enhance OutputSynthesizer with user preferences
- [ ] Build memory validation UI (user confirms/rejects patterns)
- [ ] Deploy to production

---

### Phase 3c: TP Chat (2 weeks)

**Week 1: Chat without agents**
- [ ] Implement chat action (answers from context, no agents)
- [ ] Enhance follow-up detection
- [ ] Multi-turn conversation handling
- [ ] Thread management UI

**Week 2: Polish**
- [ ] Streaming responses (SSE)
- [ ] Typing indicators
- [ ] Message edit/regenerate
- [ ] Export conversation

---

### Phase 3d: TP Synthesis (2 weeks)

**Week 1: LLM Enhancements**
- [ ] Migrate IntentParser to hybrid (rules + LLM escape hatch)
- [ ] Implement LLMAgentPlanner for complex cases
- [ ] Enhance synthesis with richer context

**Week 2: Advanced Features**
- [ ] Recursion judgment ("Should this become substrate?")
- [ ] Proactive suggestions ("I noticed you haven't researched X")
- [ ] Work triggering from chat ("Run competitor analysis")
- [ ] Analytics dashboard (TP usage metrics)

---

## Part 6: Cost & Performance Estimates

### LLM Costs (per interaction)

**Intent Parsing** (if using LLM):
- Model: Claude Haiku
- Tokens: ~500
- Cost: ~$0.0001

**Agent Selection** (if using LLM):
- Model: Claude Sonnet 4.5
- Tokens: ~1000
- Cost: ~$0.001

**Output Synthesis** (always LLM):
- Model: Claude Sonnet 4.5
- Tokens: ~2000
- Cost: ~$0.002

**Total per interaction**:
- MVP (rules + synthesis): ~$0.002
- Full LLM (intent + selection + synthesis): ~$0.003

**Monthly cost** (1000 interactions): $2-3

**Conclusion**: Very affordable for value delivered

---

### Performance

**Expected latency** (per interaction):
- Intent parsing (rules): <50ms
- Context gathering: ~200ms
- Agent execution: 10-60 seconds (depends on agent)
- Output synthesis: ~2-3 seconds

**Total**: 15-65 seconds (agent-dependent)

**Optimization opportunities**:
- Cache substrate queries
- Parallel agent execution
- Streaming synthesis responses

---

## Part 7: Risk Mitigation

### Implementation Risks

**Risk 1: LLM costs spiral**
- **Mitigation**: Start with rules, monitor costs, add LLM gradually
- **Fallback**: Disable LLM features if costs exceed threshold

**Risk 2: TP makes wrong agent decisions**
- **Mitigation**: Start with conservative decision tree, learn from feedback
- **Fallback**: User can manually override ("Just research, don't create content")

**Risk 3: Synthesis quality is poor**
- **Mitigation**: Invest in prompt engineering, user testing
- **Fallback**: Simple concatenation (Phase 3a backup)

**Risk 4: Database schema changes needed**
- **Mitigation**: Use JSONB for flexibility, minimize rigid columns
- **Fallback**: Can add columns without breaking existing data

**Risk 5: Integration with existing code breaks**
- **Mitigation**: Comprehensive integration tests, gradual rollout
- **Fallback**: Feature flag to disable TP

---

## Summary: Getting the Implementation Details Right

**What we've designed**:

1. **Clear architecture decisions** (6 critical decisions documented)
2. **Pragmatic MVP approach** (start simple, add complexity incrementally)
3. **Reuses existing infrastructure** (agent_orchestration.py, SubstrateMemoryAdapter)
4. **Flexible data model** (JSONB for evolution)
5. **Phased implementation** (3a → 3b → 3c → 3d)
6. **Full code examples** (ThinkingPartner, IntentParser, AgentSelector, etc.)
7. **Database migration** (complete SQL)
8. **API routes** (tp_routes.py)
9. **Cost analysis** (~$2-3/month for 1000 interactions)
10. **Risk mitigation** (fallbacks and monitoring)

**Confidence level**: HIGH ✅

We CAN get the implementation details right because:
- We're building on stable infrastructure (Phase 2e complete)
- We're starting with proven patterns (rule-based → LLM)
- We're reusing existing code (not rebuilding)
- We've documented every critical decision
- We have clear fallback strategies

**Next steps**:
1. Review this architecture with you
2. Address any concerns or adjustments
3. Begin Phase 3a implementation (3 weeks)
4. Iterate based on real usage