# Multi-Agent Orchestration Architecture

**Last Updated**: 2025-11-20
**Status**: Phase 2 Complete, Phase 3 (Thinking Partner) in progress

---

## Table of Contents

1. [Overview](#overview)
2. [Orchestration Patterns](#orchestration-patterns)
3. [Implementation](#implementation)
4. [Workflow Examples](#workflow-examples)
5. [Future Evolution](#future-evolution)

---

## Overview

### What is Multi-Agent Orchestration?

Multi-agent orchestration is the coordination of multiple specialized agents to complete complex tasks that require different capabilities.

**Current State (Phase 2)**:
- Specialized agents: ResearchAgent, ContentAgent, ReportingAgent
- Direct invocation via API endpoints
- Each agent operates independently
- Work outputs stored for review

**Future State (Phase 3)**:
- Thinking Partner orchestrates agents dynamically
- Workflow planning and optimization
- Cross-agent synthesis
- Pattern learning and proactive suggestions

### Orchestration Levels

**Level 1: Direct Invocation** (Current - Phase 2)
```
User → API → ResearchAgent → work_outputs
```
- User explicitly requests agent
- Single agent execution
- No cross-agent coordination

**Level 2: Thinking Partner Orchestration** (Phase 3 - MVP Complete)
```
User → TP → [decides] → ResearchAgent → work_outputs
                     → TP synthesizes → User
```
- TP decides which agent to use
- Dynamic agent selection
- Synthesized responses

**Level 3: Multi-Agent Workflows** (Future)
```
User → TP → steps_planner → [research → content → reporting]
                         → TP synthesizes → User
```
- Multi-step execution plans
- Sequential or parallel agent execution
- Cross-agent data flow

---

## Orchestration Patterns

### Pattern 1: Sequential Execution

**Use Case**: Research → Content Creation

```
Step 1: ResearchAgent.deep_dive("AI agent trends")
   ↓ produces work_outputs (findings, insights)
Step 2: ContentAgent.create(research_context=work_outputs)
   ↓ produces work_outputs (LinkedIn post)
Result: Content informed by fresh research
```

**Implementation** (Thinking Partner):
```python
# TP decides to run research first
research_outputs = await agent_orchestration({
    "agent_type": "research",
    "task": "AI agent trends"
})

# Then create content using research
content_outputs = await agent_orchestration({
    "agent_type": "content",
    "task": "Create LinkedIn post",
    "parameters": {"research_context": research_outputs}
})
```

### Pattern 2: Parallel Execution

**Use Case**: Multi-topic research

```
Parallel:
  ├─ ResearchAgent.deep_dive("Competitor A")
  ├─ ResearchAgent.deep_dive("Competitor B")
  └─ ResearchAgent.deep_dive("Competitor C")
     ↓ all produce work_outputs
Synthesis: TP combines findings
```

**Implementation** (Future):
```python
# TP plans parallel execution
import asyncio

tasks = [
    agent_orchestration({"agent_type": "research", "task": "Competitor A"}),
    agent_orchestration({"agent_type": "research", "task": "Competitor B"}),
    agent_orchestration({"agent_type": "research", "task": "Competitor C"})
]

results = await asyncio.gather(*tasks)
synthesized = tp.synthesize(results)
```

### Pattern 3: Conditional Execution

**Use Case**: Use existing research if available

```
IF recent_research_exists("AI agents"):
    content = ContentAgent.create(existing_research)
ELSE:
    research = ResearchAgent.deep_dive("AI agents")
    content = ContentAgent.create(research)
```

**Implementation** (Thinking Partner):
```python
# TP queries infrastructure
recent = await infra_reader({
    "query_type": "recent_work_requests",
    "filters": {"agent_type": "research", "limit": 5}
})

if "AI agents" in recent and not_stale(recent):
    # Use existing
    await agent_orchestration({
        "agent_type": "content",
        "task": "Create content",
        "parameters": {"use_recent_research": True}
    })
else:
    # Run fresh research
    await agent_orchestration({
        "agent_type": "research",
        "task": "AI agents"
    })
```

### Pattern 4: Iterative Refinement

**Use Case**: Content creation with feedback loop

```
Draft 1: ContentAgent.create("LinkedIn post")
   ↓ user reviews
Draft 2: ContentAgent.revise(draft_1, feedback)
   ↓ user reviews
Final: ContentAgent.finalize(draft_2)
```

**Implementation** (via work_iterations):
```python
# First draft
draft = await agent_orchestration({
    "agent_type": "content",
    "task": "Create LinkedIn post"
})

# User provides feedback via work_iterations
# work_iteration created with user feedback

# Revision
revised = await agent_orchestration({
    "agent_type": "content",
    "task": "Revise post",
    "parameters": {
        "previous_draft_id": draft.work_output_id,
        "feedback": user_feedback
    }
})
```

---

## Implementation

### Current Architecture (Phase 2)

**agent_orchestration.py**: Direct agent execution

```python
@router.post("/agents/run")
async def run_agent_task(request: AgentTaskRequest):
    # 1. Create work_request (tracks user intent)
    work_request_id = await record_work_request(...)

    # 2. Create work_ticket (tracks execution)
    work_ticket_id = await _create_work_ticket(...)

    # 3. Execute agent
    if request.agent_type == "research":
        result = await _run_research_agent(request, work_ticket_id)
    elif request.agent_type == "content":
        result = await _run_content_agent(request, work_ticket_id)
    # ...

    # 4. Write work_outputs to substrate-API
    output_write_result = write_agent_outputs(...)

    # 5. Update work_ticket status
    await _update_work_ticket_status(work_ticket_id, "completed")

    return result
```

**Key Tables**:
- `work_requests`: User's asks
- `work_tickets`: Execution tracking
- `agent_sessions`: Persistent agent conversations (ONE per basket+agent_type)
- `work_outputs`: Deliverables (in substrate-API)

### Thinking Partner Architecture (Phase 3 MVP)

**ThinkingPartnerAgent**: Orchestration via tools

```python
class ThinkingPartnerAgent(BaseAgent):
    tools = [
        agent_orchestration,  # Delegates to agents
        infra_reader,         # Queries work state
        steps_planner,        # Plans workflows
        emit_work_output      # TP's insights
    ]

    async def chat(self, user_message):
        # 1. Query memory for context
        context = await self.memory.query(user_message)

        # 2. Call Claude with tools
        response = await self.reason(
            task=user_message,
            context=context,
            tools=self.tools
        )

        # 3. Handle tool uses (if Claude wants to orchestrate)
        # 4. Synthesize response
        return response
```

**Tool: agent_orchestration**:
```python
async def _execute_agent_orchestration(self, tool_input):
    # Delegates to existing agent_orchestration.py:run_agent_task()
    from app.routes.agent_orchestration import run_agent_task

    result = await run_agent_task(
        agent_type=tool_input["agent_type"],
        task=tool_input["task"],
        basket_id=self.basket_id,
        workspace_id=self.workspace_id
    )

    return f"Agent completed: {result['work_outputs']}"
```

### Data Flow

**Direct Invocation** (Phase 2):
```
User → POST /api/agents/run
     → agent_orchestration.py
     → ResearchAgent.deep_dive()
     → work_outputs written to substrate-API
     → Response to user
```

**TP Orchestration** (Phase 3):
```
User → POST /api/tp/chat
     → ThinkingPartnerAgent.chat()
     → Claude decides to use agent_orchestration tool
     → agent_orchestration.py (same as Phase 2)
     → ResearchAgent.deep_dive()
     → work_outputs written
     → TP synthesizes response
     → Response to user
```

**Key Insight**: TP reuses existing agent_orchestration.py infrastructure via tools pattern.

---

## Workflow Examples

### Example 1: Research-Then-Content

**User Request**: "I need LinkedIn content about AI agents"

**TP Decision Process**:
```
1. Query memory: Do we have info on AI agents?
2. Query infra_reader: Recent research on this topic?
3. Decision:
   IF recent_research_exists AND not_stale:
       → Use existing, skip to content creation
   ELSE:
       → Run fresh research, then content
```

**Execution** (assuming no recent research):
```python
# TP conversation:
TP: "I don't see recent research on AI agents. Let me research first."

# TP uses agent_orchestration tool
tool_use: {
    "tool": "agent_orchestration",
    "input": {
        "agent_type": "research",
        "task": "Research AI agent trends, pricing, use cases"
    }
}

# ResearchAgent executes
# work_outputs: 5 findings, 2 insights

# TP synthesizes and continues
TP: "I found key trends. Now creating content..."

# TP uses agent_orchestration tool again
tool_use: {
    "tool": "agent_orchestration",
    "input": {
        "agent_type": "content",
        "task": "Create LinkedIn post about AI agents",
        "parameters": {
            "style": "data-driven",
            "platform": "linkedin"
        }
    }
}

# ContentAgent executes using research context
# work_outputs: 1 content_draft

# TP responds to user
TP: "Here's your LinkedIn post. I used 3 key findings from the research..."
```

### Example 2: Multi-Topic Analysis

**User Request**: "Analyze competitors A, B, and C"

**TP Workflow** (future - parallel execution):
```python
# TP uses steps_planner tool
plan = {
    "step_1": "Parallel research on all competitors",
    "step_2": "Synthesize competitive landscape",
    "step_3": "Generate recommendations"
}

# Execute Step 1 (parallel)
results = await asyncio.gather(
    agent_orchestration({"agent_type": "research", "task": "Competitor A"}),
    agent_orchestration({"agent_type": "research", "task": "Competitor B"}),
    agent_orchestration({"agent_type": "research", "task": "Competitor C"})
)

# Step 2: TP synthesizes
synthesis = tp.synthesize_competitive_landscape(results)

# Step 3: TP emits recommendations
tp.emit_work_output({
    "output_type": "recommendation",
    "title": "Competitive Positioning Strategy",
    "content": synthesis
})
```

---

## Future Evolution

### Phase 3: Full Thinking Partner

**Advanced Orchestration**:
- Multi-turn agentic loops (tool → result → continue)
- Cross-agent synthesis (combine research + content + reporting)
- Conditional workflows (if X fails, try Y)
- Parallel execution optimization

**Pattern Learning**:
- Track which workflows succeed
- Learn user preferences (platforms, styles, topics)
- Suggest proactive work ("Want me to research your competitors?")

**Recursion Judgment**:
- Decide: should work_output → substrate block?
- Create raw_dumps from derived intelligence
- Systemic updates ("Add to watchlist")

### Phase 4: Workflow Templates

**User-Configurable Workflows**:
```yaml
workflow:
  name: "Weekly Competitor Monitoring"
  schedule: "every Monday 9am"
  steps:
    - agent: research
      task: "Monitor competitors {competitors_list}"
      parallel: true
    - agent: reporting
      task: "Generate competitive landscape report"
      inputs: research_outputs
    - agent: content
      task: "Create LinkedIn post highlighting key changes"
      inputs: reporting_outputs
```

**TP Execution**:
- TP loads workflow template
- Executes steps automatically
- Notifies user when complete
- Learns from user feedback (approve/reject)

### Phase 5: Agentic Swarms

**Autonomous Multi-Agent Systems**:
- Agents collaborate without explicit orchestration
- Shared working memory
- Emergent behavior
- Self-organizing workflows

**Example**:
```
User: "Help me dominate my market"

TP spawns swarm:
  ├─ ResearchAgent (monitors competitors continuously)
  ├─ ContentAgent (creates content when opportunities detected)
  ├─ ReportingAgent (tracks performance metrics)
  └─ TP (orchestrates, learns, optimizes)

Swarm operates autonomously:
  - Research detects competitor weakness
  → Content creates response post
  → Reporting measures impact
  → TP learns what works
```

---

## Related Documentation

- **Thinking Partner**: [THINKING_PARTNER.md](THINKING_PARTNER.md)
- **Phase 2e Architecture**: [PHASE_2E_SESSION_ARCHITECTURE.md](PHASE_2E_SESSION_ARCHITECTURE.md)
- **Agent Substrate**: [AGENT_SUBSTRATE_ARCHITECTURE.md](AGENT_SUBSTRATE_ARCHITECTURE.md)

---

**Current State**: Phase 2 Complete (direct invocation), Phase 3 MVP (TP orchestration)
**Next Phase**: Frontend UI + Advanced Workflows
