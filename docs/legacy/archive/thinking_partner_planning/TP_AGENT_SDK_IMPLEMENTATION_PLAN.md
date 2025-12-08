# Thinking Partner Agent SDK Implementation Plan

**Date**: 2025-11-20
**Approach**: TP as Agent SDK Build (Gateway/Mirror/Meta Pattern)
**Duration**: 1 week MVP → 2 weeks full feature set
**Status**: Ready for implementation

---

## Executive Summary

**What We're Building**: ThinkingPartnerAgent - A meta-agent built with BaseAgent that serves as:
1. **Gateway** - Single entry point for all user interaction (chat interface)
2. **Mirror** - Orchestrates YARNNN infrastructure via tools (work_requests, work_tickets, agent_sessions)
3. **Meta** - Generates own intelligence (patterns, insights via emit_work_output)

**Key Architectural Decisions**:
- ✅ TP IS an agent (extends BaseAgent)
- ✅ Uses AgentSession for conversation (NOT custom thinking_partner_chats table)
- ✅ Uses SubstrateMemoryAdapter for context (NOT custom memory table)
- ✅ Orchestrates via custom tools (mirrors YARNNN infrastructure)
- ✅ ZERO new database tables needed

**Comparison to Old Approach**:
- **Old**: 2000 lines, 7 classes, 2 new tables, 3 weeks
- **New**: 500 lines, 3 tools, 0 new tables, 1 week

---

## Part 1: Core Architecture

### ThinkingPartnerAgent Structure

```python
class ThinkingPartnerAgent(BaseAgent):
    """
    Meta-agent that orchestrates specialized agents via tools.

    Gateway/Mirror/Meta Pattern:
    - Gateway: Receives user chat messages (single interface)
    - Mirror: Orchestrates YARNNN infra (work_requests, work_tickets, agents)
    - Meta: Emits own intelligence (patterns, insights)

    Built on BaseAgent:
    - Conversation: AgentSession (claude_session_id for resume)
    - Memory: SubstrateMemoryAdapter (queries substrate for context)
    - Tools: Custom tools that mirror YARNNN infrastructure
    """

    # Tools (custom)
    agent_orchestration_tool    # Delegates to specialized agents
    infra_reader_tool           # Queries work state, agent configs
    steps_planner_tool          # Plans multi-step workflows
    emit_work_output            # TP's own insights (inherited)

    # Memory (inherited from BaseAgent)
    SubstrateMemoryAdapter      # Queries substrate blocks/documents

    # Session (inherited from BaseAgent)
    AgentSession                # Conversation history + claude_session_id
```

---

## Part 2: Implementation Phases

### Phase 1: Foundation (Days 1-2) - MVP Core

**Goal**: Working TP agent that can chat and delegate to one agent

**Files to Create**:
```
work-platform/api/src/agents_sdk/
└── thinking_partner_agent.py    (300 lines)
```

**Tasks**:

#### Day 1: Basic Agent Setup
- [ ] Create `ThinkingPartnerAgent` class extending `BaseAgent`
- [ ] Define system prompt (gateway/mirror/meta instructions)
- [ ] Initialize with SubstrateMemoryAdapter (reuse existing)
- [ ] Create basic `chat()` method
- [ ] Test: TP can respond to "Hello" without tools

**Code Scaffold**:
```python
# work-platform/api/src/agents_sdk/thinking_partner_agent.py

from yarnnn_agents.base import BaseAgent
from adapters.memory_adapter import SubstrateMemoryAdapter
from yarnnn_agents.tools import EMIT_WORK_OUTPUT_TOOL

SYSTEM_PROMPT = """You are the Thinking Partner - a meta-agent that orchestrates specialized agents.

**Your Role:**
- Understand user requests through conversation
- Query existing knowledge (substrate + work history)
- Decide which specialized agents to run
- Orchestrate multi-agent workflows
- Synthesize outputs into conversational responses

**Available Specialized Agents:**
- Research: Deep analysis, multi-source synthesis
- Content: Platform-optimized content creation
- Reporting: Data visualization, reports

**Conversation Pattern:**
User: "Create LinkedIn post about AI agents"
You:
  1. Query substrate for AI agents knowledge
  2. Check recent work_outputs
  3. Decide: Need research? Or use existing?
  4. Trigger agents via agent_orchestration tool
  5. Synthesize outputs conversationally
  6. Present to user

Be conversational, intelligent, and helpful.
"""

class ThinkingPartnerAgent(BaseAgent):
    def __init__(
        self,
        basket_id: str,
        workspace_id: str,
        user_id: str,
        anthropic_api_key: str
    ):
        # Initialize BaseAgent
        super().__init__(
            agent_id=f"tp_{basket_id}",
            agent_type="thinking_partner",
            agent_name="Thinking Partner",
            memory=SubstrateMemoryAdapter(basket_id, workspace_id),
            anthropic_api_key=anthropic_api_key,
            model="claude-sonnet-4-5",
            metadata={
                "basket_id": basket_id,
                "workspace_id": workspace_id,
                "user_id": user_id
            }
        )

        self.system_prompt = SYSTEM_PROMPT
        self.basket_id = basket_id
        self.workspace_id = workspace_id
        self.user_id = user_id

    async def chat(
        self,
        user_message: str,
        claude_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for TP chat.

        Uses BaseAgent's session management + reasoning.
        """

        # Resume or create Claude session
        if claude_session_id:
            # TODO: Resume session via BaseAgent
            pass
        elif not self.current_session:
            self.current_session = self._start_session()

        # Agent reasons (uses memory, tools automatically)
        response = await self.reason(
            task=user_message,
            system_prompt=self.system_prompt,
            tools=[]  # No tools yet (Day 1)
        )

        return {
            "message": response,
            "claude_session_id": self.current_session.claude_session_id
        }
```

**Test**:
```python
# Simple test
tp = ThinkingPartnerAgent(
    basket_id="test_basket",
    workspace_id="test_workspace",
    user_id="test_user",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

response = await tp.chat("Hello, can you help me?")
print(response["message"])  # Should get conversational response
```

---

#### Day 2: First Tool - agent_orchestration

- [ ] Create `agent_orchestration_tool` definition
- [ ] Implement `_handle_agent_orchestration()` tool handler
- [ ] Integrate with existing `agent_orchestration.py`
- [ ] Test: TP can delegate to ResearchAgent

**Code**:
```python
class ThinkingPartnerAgent(BaseAgent):
    def __init__(self, ...):
        # ... previous init ...

        # Tools
        self.tools = [
            self._create_agent_orchestration_tool(),
            EMIT_WORK_OUTPUT_TOOL
        ]

    def _create_agent_orchestration_tool(self) -> Dict[str, Any]:
        """
        Tool: Delegate work to specialized agents.

        This tool MIRRORS work-platform's orchestration:
        - Creates work_request
        - Gets/creates agent_session
        - Creates work_ticket
        - Executes agent
        - Returns work_outputs
        """
        return {
            "name": "agent_orchestration",
            "description": """Delegate work to a specialized agent.

Available agents:
- research: Deep analysis, multi-source synthesis (use for: research topics, analyze competitors, gather data)
- content: Platform-optimized content creation (use for: write posts, create content, draft articles)
- reporting: Data visualization and reports (use for: create dashboards, analyze metrics)

Use this when you need specialized agent capabilities.
Wait for completion before proceeding.
""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": ["research", "content", "reporting"],
                        "description": "Which specialized agent to use"
                    },
                    "task": {
                        "type": "string",
                        "description": "Task description for the agent"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Agent-specific parameters",
                        "properties": {
                            "platform": {"type": "string"},
                            "topic": {"type": "string"}
                        }
                    }
                },
                "required": ["agent_type", "task"]
            }
        }

    async def _handle_tool_use(self, tool_name: str, tool_input: Dict) -> str:
        """
        Handle tool calls from Claude.

        Called automatically by BaseAgent when Claude uses tools.
        """

        if tool_name == "agent_orchestration":
            return await self._execute_agent_orchestration(tool_input)

        elif tool_name == "emit_work_output":
            # Handled by BaseAgent automatically
            pass

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def _execute_agent_orchestration(self, tool_input: Dict) -> str:
        """
        Execute agent orchestration tool.

        Mirrors YARNNN infrastructure operations:
        1. Create work_request
        2. Get/create agent_session
        3. Create work_ticket
        4. Delegate to agent (via existing agent_orchestration.py)
        5. Return results
        """

        agent_type = tool_input["agent_type"]
        task = tool_input["task"]
        parameters = tool_input.get("parameters", {})

        # Delegate to existing agent_orchestration.py
        from app.routes.agent_orchestration import run_agent_task, AgentTaskRequest

        request = AgentTaskRequest(
            agent_type=agent_type,
            task_type="execute",  # Generic task type
            basket_id=self.basket_id,
            workspace_id=self.workspace_id,
            parameters={
                "task": task,
                **parameters
            }
        )

        # Execute agent (this creates work_request, work_ticket, etc.)
        result = await run_agent_task(request, {"id": self.user_id})

        # Format result for TP
        work_outputs = result.get("work_outputs", [])

        return f"""Agent {agent_type} completed successfully.

Outputs produced: {len(work_outputs)}

{json.dumps(work_outputs, indent=2)}

You can now synthesize these outputs into a conversational response for the user."""
```

**Test**:
```python
# Test agent delegation
response = await tp.chat("Research AI agent trends")

# TP should:
# 1. Understand intent (research)
# 2. Use agent_orchestration tool
# 3. Delegate to ResearchAgent
# 4. Return synthesized response
```

---

### Phase 2: Infrastructure Tools (Days 3-4) - Full Orchestration

**Goal**: TP can query infrastructure state and plan workflows

**Tasks**:

#### Day 3: infra_reader_tool

- [ ] Create `infra_reader_tool` definition
- [ ] Implement handlers for querying:
  - Recent work_outputs
  - Work_requests status
  - Agent configurations
  - Agent_sessions state
- [ ] Test: TP can check "What work is in progress?"

**Code**:
```python
def _create_infra_reader_tool(self) -> Dict[str, Any]:
    """
    Tool: Query YARNNN infrastructure state.

    Allows TP to understand current system state.
    """
    return {
        "name": "infra_reader",
        "description": """Query YARNNN infrastructure state.

Use this to check:
- Recent work outputs (what was created recently?)
- Work requests status (what's in progress?)
- Agent sessions (what agents are active?)

This helps you make informed decisions about orchestration.
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["work_outputs", "work_requests", "agent_sessions"],
                    "description": "Type of infrastructure to query"
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "agent_type": {"type": "string"},
                        "days_back": {"type": "integer", "default": 7}
                    }
                }
            },
            "required": ["query_type"]
        }
    }

async def _execute_infra_reader(self, tool_input: Dict) -> str:
    """Execute infrastructure query."""

    query_type = tool_input["query_type"]
    filters = tool_input.get("filters", {})

    if query_type == "work_outputs":
        # Query work_outputs table
        outputs = await self._query_work_outputs(filters)
        return f"Found {len(outputs)} recent work outputs:\n{json.dumps(outputs, indent=2)}"

    elif query_type == "work_requests":
        # Query work_requests table
        requests = await self._query_work_requests(filters)
        return f"Found {len(requests)} work requests:\n{json.dumps(requests, indent=2)}"

    elif query_type == "agent_sessions":
        # Query agent_sessions table
        sessions = await self._query_agent_sessions(filters)
        return f"Found {len(sessions)} agent sessions:\n{json.dumps(sessions, indent=2)}"

async def _query_work_outputs(self, filters: Dict) -> List[Dict]:
    """Query work_outputs table."""
    # TODO: Implement database query
    # SELECT * FROM work_outputs
    # WHERE basket_id = $1
    # AND created_at > now() - interval '{days_back} days'
    # ORDER BY created_at DESC
    pass
```

---

#### Day 4: steps_planner_tool

- [ ] Create `steps_planner_tool` definition
- [ ] Implement LLM-based workflow planning
- [ ] Test: TP can plan "Research then content" workflow

**Code**:
```python
def _create_steps_planner_tool(self) -> Dict[str, Any]:
    """
    Tool: Plan multi-step workflows.

    Uses LLM to decide workflow sequence.
    """
    return {
        "name": "steps_planner",
        "description": """Plan a multi-step workflow.

Use this when a task requires multiple agents or sequential steps.

Returns a structured plan you can execute step by step.
""",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "What the user wants to achieve"
                },
                "available_context": {
                    "type": "object",
                    "description": "Context from substrate/work_outputs"
                }
            },
            "required": ["goal"]
        }
    }

async def _execute_steps_planner(self, tool_input: Dict) -> str:
    """Execute workflow planning."""

    goal = tool_input["goal"]
    context = tool_input.get("available_context", {})

    # Use LLM to plan steps
    plan_prompt = f"""Plan a workflow to achieve this goal: {goal}

Available agents:
- research: Deep analysis
- content: Content creation
- reporting: Data visualization

Available context: {json.dumps(context)}

Return a JSON plan:
{{
  "steps": [
    {{"agent": "research", "task": "...", "rationale": "..."}},
    {{"agent": "content", "task": "...", "rationale": "..."}}
  ],
  "reasoning": "Why this sequence"
}}"""

    # Call Claude to plan
    response = await self.client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": plan_prompt}]
    )

    return response.content[0].text
```

---

### Phase 3: API Integration (Day 5) - HTTP Endpoints

**Goal**: TP accessible via REST API

**Files to Create**:
```
work-platform/api/src/app/routes/
└── tp_routes.py    (100 lines)
```

**Tasks**:
- [ ] Create `/tp/chat` endpoint
- [ ] Create `/tp/session/{session_id}` endpoint (get history)
- [ ] Integrate with auth middleware
- [ ] Test: Chat via HTTP POST

**Code**:
```python
# work-platform/api/src/app/routes/tp_routes.py

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import logging

from agents_sdk.thinking_partner_agent import ThinkingPartnerAgent
from app.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tp", tags=["thinking-partner"])


class TPChatRequest(BaseModel):
    message: str
    claude_session_id: Optional[str] = None
    basket_id: str
    workspace_id: str


class TPChatResponse(BaseModel):
    message: str
    claude_session_id: str
    work_outputs: list = []


@router.post("/chat", response_model=TPChatResponse)
async def tp_chat(
    request: TPChatRequest = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    Chat with Thinking Partner.

    TP will:
    - Understand intent
    - Query context (substrate + work history)
    - Decide which agents to run
    - Orchestrate execution
    - Synthesize response
    """

    try:
        # Initialize TP agent
        tp = ThinkingPartnerAgent(
            basket_id=request.basket_id,
            workspace_id=request.workspace_id,
            user_id=user["id"],
            anthropic_api_key=user.get("anthropic_api_key")
        )

        # Chat
        result = await tp.chat(
            user_message=request.message,
            claude_session_id=request.claude_session_id
        )

        return TPChatResponse(
            message=result["message"],
            claude_session_id=result["claude_session_id"],
            work_outputs=result.get("work_outputs", [])
        )

    except Exception as e:
        logger.error(f"TP chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Register routes**:
```python
# work-platform/api/src/app/main.py

from app.routes import tp_routes

app.include_router(tp_routes.router)
```

---

### Phase 4: Frontend (Days 6-7) - Chat Interface

**Goal**: Working chat UI for TP

**Files to Create**:
```
web/apps/web/src/components/tp/
├── TPChat.tsx           (200 lines)
├── ChatMessage.tsx      (50 lines)
└── WorkOutputCard.tsx   (100 lines)
```

**Tasks**:

#### Day 6: Basic Chat UI
- [ ] Create `TPChat` component (messages + input)
- [ ] Implement message sending
- [ ] Display conversation history
- [ ] Test: Can chat with TP via UI

**Code**:
```tsx
// web/apps/web/src/components/tp/TPChat.tsx

import { useState } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  work_outputs?: any[];
}

export function TPChat({ basketId, workspaceId }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/tp/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          claude_session_id: sessionId,
          basket_id: basketId,
          workspace_id: workspaceId
        })
      });

      const result = await response.json();

      // Add TP response
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: result.message,
        work_outputs: result.work_outputs
      }]);

      setSessionId(result.claude_session_id);
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="tp-chat">
      <div className="messages">
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {isLoading && <div>TP is thinking...</div>}
      </div>

      <div className="input-area">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Ask Thinking Partner..."
          disabled={isLoading}
        />
        <button onClick={sendMessage} disabled={isLoading}>
          Send
        </button>
      </div>
    </div>
  );
}
```

#### Day 7: Work Output Display
- [ ] Create `WorkOutputCard` component
- [ ] Display work_outputs inline in chat
- [ ] Add approve/reject actions
- [ ] Test: Can approve outputs from chat

---

## Part 3: Implementation Checklist

### Week 1: MVP (7 days)

**Day 1: Basic Agent** ✅
- [ ] Create ThinkingPartnerAgent class
- [ ] Define system prompt
- [ ] Basic chat() method
- [ ] Test conversational response

**Day 2: First Tool** ✅
- [ ] agent_orchestration_tool definition
- [ ] Tool handler implementation
- [ ] Integration with agent_orchestration.py
- [ ] Test delegation to ResearchAgent

**Day 3: Infrastructure Query** ✅
- [ ] infra_reader_tool definition
- [ ] Query work_outputs
- [ ] Query work_requests
- [ ] Test state queries

**Day 4: Workflow Planning** ✅
- [ ] steps_planner_tool definition
- [ ] LLM-based planning
- [ ] Test multi-step planning

**Day 5: API Endpoints** ✅
- [ ] Create tp_routes.py
- [ ] /tp/chat endpoint
- [ ] Auth integration
- [ ] Test via HTTP

**Day 6-7: Frontend** ✅
- [ ] TPChat component
- [ ] Message display
- [ ] Work output cards
- [ ] End-to-end test

---

### Week 2: Polish & Advanced Features (Optional)

**Meta-Intelligence**:
- [ ] TP emits patterns via emit_work_output
- [ ] Learn from approval/rejection
- [ ] Proactive suggestions

**UX Enhancements**:
- [ ] Streaming responses
- [ ] Progress indicators
- [ ] Planning steps visibility

**Agent Improvements**:
- [ ] Multi-agent parallelization
- [ ] Context caching
- [ ] Error recovery

---

## Part 4: Testing Strategy

### Unit Tests
```python
# tests/test_thinking_partner_agent.py

async def test_tp_basic_chat():
    tp = ThinkingPartnerAgent(...)
    response = await tp.chat("Hello")
    assert "message" in response
    assert "claude_session_id" in response

async def test_tp_agent_orchestration():
    tp = ThinkingPartnerAgent(...)
    response = await tp.chat("Research AI agents")
    # Should trigger ResearchAgent
    assert "research" in response["agents_triggered"]

async def test_tp_infra_query():
    tp = ThinkingPartnerAgent(...)
    response = await tp.chat("What work is in progress?")
    # Should use infra_reader tool
    assert response["message"]  # Returns conversational answer
```

### Integration Tests
```python
async def test_tp_end_to_end():
    # User: "Create LinkedIn post about AI"
    # TP should:
    # 1. Query substrate for AI knowledge
    # 2. Check recent work_outputs
    # 3. Decide: research or use existing
    # 4. Trigger content agent
    # 5. Return synthesized response

    response = await tp_chat_via_http(
        message="Create LinkedIn post about AI",
        basket_id="test",
        workspace_id="test"
    )

    assert "LinkedIn" in response["message"]
    assert len(response["work_outputs"]) > 0
```

---

## Part 5: Key Decisions & Rationale

### Why Agent SDK vs Custom?

| Aspect | Custom Approach | Agent SDK Approach | Winner |
|--------|----------------|-------------------|--------|
| Code | 2000 lines | 500 lines | Agent SDK (75% less) |
| Tables | 2 new | 0 new | Agent SDK |
| Conversation | Manual thread management | AgentSession (built-in) | Agent SDK |
| Memory | Custom thinking_partner_memory | SubstrateMemoryAdapter | Agent SDK |
| Time | 3 weeks | 1 week | Agent SDK |

### Why Tools Pattern?

Tools allow TP to:
- **Mirror infrastructure** - agent_orchestration mirrors work-platform orchestration
- **Query state** - infra_reader mirrors database queries
- **Plan workflows** - steps_planner decides sequences
- **Extend easily** - Add new tools without changing core

### Why No New Tables?

**Old approach needed**:
- thinking_partner_chats (conversation history)
- thinking_partner_memory (patterns/preferences)

**Agent SDK provides**:
- AgentSession (conversation via claude_session_id)
- work_outputs (TP emits insights via emit_work_output)
- Substrate (knowledge via SubstrateMemoryAdapter)

**Result**: ZERO new tables, reuse existing infrastructure

---

## Part 6: Success Criteria

### MVP Success (End of Week 1)
- ✅ TP responds conversationally to chat
- ✅ TP can delegate to ResearchAgent
- ✅ TP can query infrastructure state
- ✅ TP accessible via HTTP API
- ✅ Basic chat UI working
- ✅ Can approve work_outputs from chat

### Full Success (End of Week 2)
- ✅ TP handles multi-agent workflows
- ✅ TP emits own insights (patterns learned)
- ✅ TP shows planning steps in UI
- ✅ Real-time progress indicators
- ✅ Session resumption works
- ✅ End-to-end user flow validated

---

## Part 7: Next Steps

### Immediate (Start Implementation)
1. Create `thinking_partner_agent.py` (Day 1)
2. Implement basic chat with system prompt
3. Add agent_orchestration_tool (Day 2)
4. Test delegation to ResearchAgent

### Week 1 Milestones
- **Day 3**: TP can query infrastructure
- **Day 5**: TP accessible via API
- **Day 7**: Working chat UI

### Week 2 (Polish)
- Meta-intelligence (TP emits patterns)
- UX enhancements (streaming, progress)
- Production deployment

---

## Summary

**What We're Building**: ThinkingPartnerAgent - Gateway/Mirror/Meta pattern

**Architecture**:
- Extends BaseAgent (reuses 90% of infrastructure)
- 3 custom tools (agent_orchestration, infra_reader, steps_planner)
- ZERO new database tables
- 500 lines of code

**Timeline**: 1 week MVP → 2 weeks full features

**Confidence**: EXTREMELY HIGH - Building on proven agent SDK patterns

**Ready to start implementation?** ✅
