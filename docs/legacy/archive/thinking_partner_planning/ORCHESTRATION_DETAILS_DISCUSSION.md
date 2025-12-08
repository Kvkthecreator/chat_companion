# Orchestration Details Discussion

**Date**: 2025-11-20
**Context**: Deep dive into hybrid orchestration pattern mechanics
**Goal**: Answer specific questions about data flow, ownership, and agent responsibility boundaries

---

## Your Three Questions

### Q1: Data Flow - Direct Passing vs Round-Trip?

**Your Question**: "So the results from say the researcher agent still pass through back to the substrate, and round-trip or is direct passing done? or both?"

**Answer**: **Both - but at different stages of the lifecycle**

Let me walk through the exact data flow:

---

### Scenario: User Requests "Create LinkedIn post about AI agent trends"

#### Current Implementation (Single Agent - No Multi-Agent Yet)

**What Actually Happens Today** (from [agent_orchestration.py:234-376](work-platform/api/src/app/routes/agent_orchestration.py#L234-L376)):

```python
# POST /agents/run with agent_type="research", task_type="deep_dive"

# Step 1: Create work_ticket
work_ticket_id = await _create_work_ticket(
    basket_id=basket_id,
    agent_type="research",
    task_intent="research:deep_dive - topic: AI agent trends"
)

# Step 2: Execute agent
agent = ResearchAgentSDK(basket_id, workspace_id, work_ticket_id)
result = await agent.deep_dive("AI agent trends")
# result = {
#     "work_outputs": [
#         {"output_type": "finding", "title": "...", "body": "..."},
#         {"output_type": "insight", "title": "...", "body": "..."}
#     ],
#     "source_block_ids": ["block_123", "block_456"]
# }

# Step 3: Write outputs to work-platform DB
output_write_result = write_agent_outputs(
    basket_id=basket_id,
    work_ticket_id=work_ticket_id,
    agent_type="research",
    outputs=result["work_outputs"]
)
# Outputs stored in work_outputs table (work-platform DB)

# Step 4: Update work_ticket
await _update_work_ticket_status(work_ticket_id, "completed")

# Step 5: Return to user
return AgentTaskResponse(
    status="completed",
    result=result,  # Includes work_outputs
    outputs_written=5
)
```

**Data Flow Visualization (Current - Single Agent)**:

```
User Request
    ↓
agent_orchestration.py (work-platform)
    ↓
ResearchAgentSDK.deep_dive()
    ├─ Queries substrate via memory_adapter (READ from substrate-API)
    │  └─ Returns existing knowledge blocks
    ├─ Calls Claude with web_search
    │  └─ Returns research findings
    └─ Returns work_outputs (in-memory dict)
    ↓
write_agent_outputs() (work-platform service)
    ↓
work_outputs table (work-platform DB) ← WRITE
    ↓
Return to user (JSON response with work_outputs)
```

**Key Point**: **NO round-trip to substrate storage** - outputs stay in work-platform DB.

---

#### Proposed Multi-Agent Implementation (Hybrid Pattern)

**Scenario**: Research → Content workflow

**Option A: Pure Round-Trip (NOT RECOMMENDED)**

```python
# Step 1: Research agent
research_result = await research_agent.deep_dive(topic)

# Step 2: Write outputs to work_outputs table
research_output_ids = await write_agent_outputs(research_result["work_outputs"])

# Step 3: Wait for user approval
approved = await wait_for_approval(research_output_ids)

# Step 4: Absorb into substrate
substrate_block_ids = await substrate_api.create_blocks_from_outputs(research_output_ids)

# Step 5: Content agent queries substrate for research findings
content_agent = ContentAgentSDK(...)
# Inside ContentAgent.create():
#   research_findings = await self.memory.query("AI agent trends research")
#   ↑ This queries substrate, finds the blocks we just created

result = await content_agent.create(platform="linkedin", topic="AI agent trends")
```

**Problems with Pure Round-Trip**:
- ❌ **Latency**: Write to DB → Read from DB (unnecessary I/O)
- ❌ **Inefficiency**: Content agent must query/search for what orchestrator already has
- ❌ **Brittleness**: Query might not find the right blocks (semantic search uncertainty)
- ❌ **Complexity**: Timing issues (what if blocks not indexed yet?)

---

**Option B: Pure Direct Passing (NOT RECOMMENDED)**

```python
# Step 1: Research agent
research_result = await research_agent.deep_dive(topic)

# Step 2: Pass directly to content agent (no storage)
result = await content_agent.create(
    platform="linkedin",
    topic="AI agent trends",
    research_context=json.dumps(research_result["work_outputs"])
)

# Step 3: Only store final outputs
await write_agent_outputs(result["work_outputs"])
```

**Problems with Pure Direct Passing**:
- ❌ **No audit trail**: Research findings lost (not stored)
- ❌ **No supervision**: Can't review research before content creation
- ❌ **No reuse**: Next content request re-does research
- ❌ **No provenance**: Can't trace "how did we get this content?"

---

**Option C: Hybrid (RECOMMENDED)**

```python
async def research_then_content_workflow(topic, platform):
    """
    Hybrid: Store everything + Pass directly when needed
    """

    # === RESEARCH PHASE ===

    # Step 1: Execute research agent
    research_agent = ResearchAgentSDK(basket_id, workspace_id, work_ticket_id_1)
    research_result = await research_agent.deep_dive(topic)

    # Step 2: STORE outputs immediately (audit trail)
    research_output_ids = await write_agent_outputs(
        basket_id=basket_id,
        work_ticket_id=work_ticket_id_1,
        agent_type="research",
        outputs=research_result["work_outputs"]
    )
    # ✅ Outputs now in work_outputs table (work-platform DB)

    # Step 3: USER SUPERVISION CHECKPOINT
    # User sees outputs in UI, can approve/reject
    approved = await wait_for_user_approval(research_output_ids)

    if not approved:
        return {"status": "rejected", "step": "research"}

    # Step 4: ABSORB into substrate (optional - for future reuse)
    # This is ASYNC, doesn't block content creation
    asyncio.create_task(
        substrate_api.absorb_approved_outputs(research_output_ids)
    )
    # ✅ Outputs will become substrate blocks (substrate-API DB)
    # ✅ But we don't wait for this - content agent proceeds immediately

    # === CONTENT PHASE ===

    # Step 5: Execute content agent with DIRECT context
    content_agent = ContentAgentSDK(basket_id, workspace_id, work_ticket_id_2)

    # HYBRID: Pass research findings DIRECTLY (no query needed)
    result = await content_agent.create(
        platform=platform,
        topic=topic,
        research_context=json.dumps(research_result["work_outputs"])  # Direct!
    )
    # ✅ ContentAgent gets research findings instantly (no substrate query)
    # ✅ ContentAgent ALSO queries substrate for brand voice (separate concern)

    # Step 6: STORE content outputs with PROVENANCE
    content_output_ids = await write_agent_outputs(
        basket_id=basket_id,
        work_ticket_id=work_ticket_id_2,
        agent_type="content",
        outputs=result["work_outputs"],
        source_output_ids=research_output_ids  # Provenance link!
    )
    # ✅ Outputs stored with lineage: content ← research

    return {
        "status": "completed",
        "research_output_ids": research_output_ids,
        "content_output_ids": content_output_ids,
        "provenance": {
            "research": research_output_ids,
            "content": content_output_ids,
            "lineage": f"{research_output_ids} → {content_output_ids}"
        }
    }
```

**Data Flow Visualization (Hybrid)**:

```
RESEARCH PHASE:
──────────────
User Request
    ↓
Workflow Orchestrator (work-platform)
    ↓
ResearchAgent.deep_dive()
    ├─ READ substrate (brand voice, past research)
    └─ Returns work_outputs (in-memory)
    ↓
WRITE to work_outputs table (work-platform DB) ← STORED
    ↓
User approval checkpoint
    ↓
ASYNC: Absorb to substrate blocks (substrate-API DB) ← PERMANENT KNOWLEDGE
                                                         (doesn't block next step)

CONTENT PHASE:
──────────────
Workflow Orchestrator
    ├─ Has research_result["work_outputs"] in memory
    └─ Passes DIRECTLY to ContentAgent (no query)
    ↓
ContentAgent.create(research_context=...)
    ├─ READ substrate (brand voice examples)
    ├─ Uses research_context (direct - no query)
    └─ Returns work_outputs (in-memory)
    ↓
WRITE to work_outputs table (work-platform DB) ← STORED
    ├─ Links to research outputs via source_output_ids
    └─ Provenance chain preserved
```

**Answer Summary**:
- **Direct passing**: Research → Content (in-memory, low latency)
- **Storage**: Both research and content outputs written to work_outputs table
- **Round-trip**: NOT for immediate workflow, but substrate absorption happens async for future reuse

---

### Q2: Who/What Does Orchestration in work-platform?

**Your Question**: "Who and what exactly then would do the orchestration within the work-platform. yarnnn orchestration is currently about agent config, factory, general orchestration but not multi-agent, cross-agent..."

**Current State Analysis**:

#### What [agent_orchestration.py](work-platform/api/src/app/routes/agent_orchestration.py) Currently Does:

**✅ Single-Agent Orchestration**:
1. Auth/permissions (verify_jwt, check workspace access)
2. Work ticket creation/tracking
3. Agent factory (ResearchAgentSDK, ContentAgentSDK, ReportingAgentSDK)
4. Knowledge module loading
5. Agent execution (calls agent.deep_dive(), agent.create(), etc.)
6. Output storage (write_agent_outputs())
7. Status tracking (work_ticket updates)

**❌ Does NOT Do (Yet)**:
1. Multi-agent workflows (research → content sequences)
2. Cross-agent context passing
3. Approval checkpoints between agents
4. Conditional execution (if research approved, then content)
5. Parallel agent execution
6. Workflow state management

---

#### Proposed Architecture: Workflow Layer

**New Component**: `work-platform/api/src/app/workflows/`

```
work-platform/api/src/app/
├─ routes/
│   ├─ agent_orchestration.py  ← Single-agent execution (KEEP)
│   └─ workflows.py             ← Multi-agent workflows (NEW)
├─ workflows/                   ← Workflow definitions (NEW)
│   ├─ __init__.py
│   ├─ base.py                  ← Base workflow class
│   ├─ research_then_content.py ← Research → Content workflow
│   ├─ content_with_research.py ← Content with optional research
│   └─ report_generation.py     ← Report with data gathering
└─ services/
    ├─ work_output_service.py   ← Output storage (EXISTS)
    └─ workflow_engine.py       ← Workflow execution (NEW)
```

**Example: Base Workflow Class**

```python
# work-platform/api/src/app/workflows/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

class WorkflowStep(Enum):
    """Workflow step types"""
    AGENT_EXECUTION = "agent_execution"
    USER_APPROVAL = "user_approval"
    DATA_TRANSFORM = "data_transform"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"

class WorkflowState:
    """Tracks workflow execution state"""
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self.current_step = 0
        self.steps_completed = []
        self.steps_failed = []
        self.intermediate_outputs = {}  # Store outputs between steps
        self.work_ticket_ids = []
        self.work_output_ids = []

class BaseWorkflow(ABC):
    """
    Base class for multi-agent workflows.

    Workflow owns:
    - Step sequencing
    - Context passing between agents
    - Approval checkpoints
    - Error handling and rollback

    Workflow does NOT own:
    - Agent execution (delegates to agents)
    - Output storage (delegates to services)
    - Substrate operations (delegates to substrate-API)
    """

    def __init__(
        self,
        basket_id: str,
        workspace_id: str,
        user_id: str
    ):
        self.basket_id = basket_id
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.state = None

    @abstractmethod
    async def define_steps(self) -> List[Dict[str, Any]]:
        """
        Define workflow steps (to be implemented by subclasses).

        Returns:
            List of step definitions
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the workflow.

        Returns:
            Workflow result
        """
        pass

    async def _execute_agent_step(
        self,
        agent_type: str,
        method: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute single agent step"""
        # Delegate to agent_orchestration.py single-agent logic
        pass

    async def _wait_for_approval(
        self,
        output_ids: List[str],
        timeout_seconds: Optional[int] = None
    ) -> bool:
        """Wait for user approval of outputs"""
        # Implement approval logic (webhook, polling, etc.)
        pass

    async def _store_outputs(
        self,
        outputs: List[Dict],
        work_ticket_id: str,
        source_output_ids: Optional[List[str]] = None
    ) -> List[str]:
        """Store outputs with provenance"""
        # Delegate to work_output_service
        pass
```

**Example: Research → Content Workflow**

```python
# work-platform/api/src/app/workflows/research_then_content.py

from .base import BaseWorkflow, WorkflowStep, WorkflowState
from agents_sdk import ResearchAgentSDK, ContentAgentSDK
from app.services.work_output_service import write_agent_outputs
import logging

logger = logging.getLogger(__name__)

class ResearchThenContentWorkflow(BaseWorkflow):
    """
    Workflow: Research → User Approval → Content Creation

    Steps:
    1. Execute research agent
    2. Store research outputs
    3. Wait for user approval
    4. Execute content agent with research context
    5. Store content outputs with provenance
    """

    async def define_steps(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": WorkflowStep.AGENT_EXECUTION,
                "agent_type": "research",
                "method": "deep_dive",
                "name": "research_phase"
            },
            {
                "type": WorkflowStep.USER_APPROVAL,
                "approval_subject": "research_outputs",
                "name": "approve_research"
            },
            {
                "type": WorkflowStep.AGENT_EXECUTION,
                "agent_type": "content",
                "method": "create",
                "context_from": "research_phase",  # Get context from previous step
                "name": "content_creation"
            }
        ]

    async def execute(
        self,
        topic: str,
        platform: str,
        require_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Execute research → content workflow.

        Args:
            topic: Research topic
            platform: Content platform (twitter, linkedin, etc.)
            require_approval: Whether to require user approval between steps

        Returns:
            Workflow result with all outputs and provenance
        """

        self.state = WorkflowState(workflow_id=f"rtc_{topic}_{platform}")

        logger.info(f"Starting Research→Content workflow: {topic} → {platform}")

        # ========== STEP 1: RESEARCH ==========

        logger.info("Step 1: Research phase")

        # Create work ticket for research
        research_ticket_id = await self._create_work_ticket(
            agent_type="research",
            task_intent=f"Research for content: {topic}"
        )

        # Execute research agent
        research_agent = ResearchAgentSDK(
            basket_id=self.basket_id,
            workspace_id=self.workspace_id,
            work_ticket_id=research_ticket_id
        )

        research_result = await research_agent.deep_dive(topic)

        # Store research outputs
        research_output_ids = await write_agent_outputs(
            basket_id=self.basket_id,
            work_ticket_id=research_ticket_id,
            agent_type="research",
            outputs=research_result["work_outputs"]
        )

        logger.info(f"Research complete: {len(research_output_ids)} outputs stored")

        # Store in workflow state
        self.state.intermediate_outputs["research_result"] = research_result
        self.state.work_output_ids.extend(research_output_ids)
        self.state.steps_completed.append("research_phase")

        # ========== STEP 2: APPROVAL ==========

        if require_approval:
            logger.info("Step 2: Awaiting user approval")

            approved = await self._wait_for_approval(
                output_ids=research_output_ids,
                timeout_seconds=3600  # 1 hour timeout
            )

            if not approved:
                logger.warning("Research outputs rejected by user")
                return {
                    "status": "rejected",
                    "step": "research_approval",
                    "research_output_ids": research_output_ids
                }

            self.state.steps_completed.append("approve_research")

        # ========== STEP 3: CONTENT CREATION ==========

        logger.info("Step 3: Content creation phase")

        # Create work ticket for content
        content_ticket_id = await self._create_work_ticket(
            agent_type="content",
            task_intent=f"Create {platform} content about: {topic}"
        )

        # Execute content agent with research context (DIRECT PASSING)
        content_agent = ContentAgentSDK(
            basket_id=self.basket_id,
            workspace_id=self.workspace_id,
            work_ticket_id=content_ticket_id
        )

        # Build research context for direct passing
        research_context = self._build_research_context(research_result)

        content_result = await content_agent.create(
            platform=platform,
            topic=topic,
            research_context=research_context  # Direct passing!
        )

        # Store content outputs WITH PROVENANCE
        content_output_ids = await write_agent_outputs(
            basket_id=self.basket_id,
            work_ticket_id=content_ticket_id,
            agent_type="content",
            outputs=content_result["work_outputs"],
            source_output_ids=research_output_ids  # Provenance!
        )

        logger.info(f"Content complete: {len(content_output_ids)} outputs stored")

        self.state.work_output_ids.extend(content_output_ids)
        self.state.steps_completed.append("content_creation")

        # ========== WORKFLOW COMPLETE ==========

        return {
            "status": "completed",
            "workflow": "research_then_content",
            "topic": topic,
            "platform": platform,
            "steps_completed": self.state.steps_completed,
            "research": {
                "work_ticket_id": research_ticket_id,
                "output_ids": research_output_ids,
                "output_count": len(research_output_ids)
            },
            "content": {
                "work_ticket_id": content_ticket_id,
                "output_ids": content_output_ids,
                "output_count": len(content_output_ids)
            },
            "provenance": {
                "lineage": f"{research_output_ids} → {content_output_ids}",
                "all_outputs": self.state.work_output_ids
            }
        }

    def _build_research_context(self, research_result: Dict) -> str:
        """
        Transform research outputs into context string for content agent.

        This is where DIRECT PASSING happens - we serialize the
        research findings into a format the content agent expects.
        """
        import json

        research_findings = [
            {
                "title": wo["title"],
                "body": wo["body"],
                "confidence": wo.get("confidence", 0.5),
                "output_type": wo["output_type"]
            }
            for wo in research_result["work_outputs"]
        ]

        return json.dumps(research_findings, indent=2)
```

**API Route for Workflows**

```python
# work-platform/api/src/app/routes/workflows.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.jwt import verify_jwt
from app.workflows.research_then_content import ResearchThenContentWorkflow

router = APIRouter(prefix="/workflows", tags=["workflows"])

class ResearchThenContentRequest(BaseModel):
    basket_id: str
    topic: str
    platform: str
    require_approval: bool = True

@router.post("/research-then-content")
async def run_research_then_content(
    request: ResearchThenContentRequest,
    user: dict = Depends(verify_jwt)
):
    """
    Execute research → content workflow.

    This is multi-agent orchestration - coordinates ResearchAgent
    and ContentAgent with approval checkpoint between them.
    """
    user_id = user.get("sub") or user.get("user_id")
    workspace_id = await _get_workspace_id_for_user(user_id)

    # Create workflow instance
    workflow = ResearchThenContentWorkflow(
        basket_id=request.basket_id,
        workspace_id=workspace_id,
        user_id=user_id
    )

    # Execute workflow
    result = await workflow.execute(
        topic=request.topic,
        platform=request.platform,
        require_approval=request.require_approval
    )

    return result
```

---

**Answer Summary**:

**Who does orchestration**: New `workflows/` module in work-platform

**What it orchestrates**:
1. **Step sequencing**: Research → Approval → Content
2. **Context passing**: Extracts research outputs, passes to content agent
3. **Approval gates**: User checkpoints between steps
4. **Provenance tracking**: Links outputs via source_output_ids
5. **Error handling**: Rollback, retry logic

**What it does NOT do**:
1. Agent execution (delegates to ResearchAgentSDK, ContentAgentSDK)
2. Output storage (delegates to work_output_service)
3. Substrate operations (delegates to substrate-API)

---

### Q3: Agent Responsibility Boundaries - Should ContentAgent Have Research?

**Your Question**: "Should the content agent have its own researching sub feature (think, web search for social media tracking), thus up to discussion for potential re-shuffling of responsibilities?"

This is the MOST important architectural question. Let me analyze carefully.

---

#### Current Agent Responsibilities

**ResearchAgentSDK** ([research_agent.py](work-platform/api/src/agents_sdk/research_agent.py)):
- ✅ web_search (trending topics, competitor analysis)
- ✅ web_fetch (specific URL analysis)
- ✅ Memory adapter (query substrate for past research)
- ✅ Subagents: web_monitor, competitor_tracker, social_listener, analyst
- ✅ Output: findings, insights, recommendations

**ContentAgentSDK** ([content_agent.py](work-platform/api/src/agents_sdk/content_agent.py)):
- ❌ NO web_search (after refactor, will be added)
- ❌ NO web_fetch
- ✅ Memory adapter (query substrate for brand voice)
- ❌ NO subagents
- ✅ Output: content drafts (text), files (DOCX, PPTX after refactor)

---

#### The Question: Should ContentAgent Also Search the Web?

**Two Architectural Patterns**:

**Pattern A: Focused Agents (Current Direction)**
```
ResearchAgent = Information gathering specialist
  ├─ Deep research
  ├─ Trend analysis
  ├─ Competitor tracking
  └─ Web search/fetch

ContentAgent = Creative production specialist
  ├─ Platform-specific formatting
  ├─ Brand voice matching
  ├─ Content generation
  └─ Uses research from ResearchAgent OR substrate
```

**Pattern B: Self-Sufficient Agents**
```
ResearchAgent = Information gathering specialist
  ├─ Deep research
  ├─ Trend analysis
  ├─ Competitor tracking
  └─ Web search/fetch

ContentAgent = Self-sufficient content creator
  ├─ Platform-specific formatting
  ├─ Brand voice matching
  ├─ Content generation
  ├─ ALSO: Web search for trending hashtags
  ├─ ALSO: Web fetch for competitor posts
  └─ Does its own research (doesn't need ResearchAgent)
```

---

#### Analysis: Focused vs Self-Sufficient

**Arguments FOR Self-Sufficient (ContentAgent does own research)**:

1. **Lower latency**: No need to wait for ResearchAgent
2. **Simpler workflows**: Single agent call instead of multi-step
3. **Autonomy**: ContentAgent can work independently
4. **Real-world analogy**: Content creators DO research trending hashtags themselves

**Arguments AGAINST Self-Sufficient (Keep agents focused)**:

1. **Duplication of capability**: Both agents have web_search
2. **Duplication of code**: Search logic in two places
3. **Inconsistent research quality**: ContentAgent's research may be shallower
4. **Loss of specialization**: ResearchAgent's deep analysis is its value-add
5. **Harder to maintain**: Changes to research methodology need updates in 2 places
6. **Violates single responsibility**: Content creation ≠ Research

---

#### Recommended Approach: **Hybrid with Tool-Level Granularity**

**Principle**: Give agents the tools they need for their PRIMARY job, not ALL tools.

**ResearchAgentSDK** (Information Gathering):
```python
tools = [
    EMIT_WORK_OUTPUT_TOOL,
    {"type": "web_search_20250305", "name": "web_search"},
    {"type": "web_fetch_20250305", "name": "web_fetch"},
    # Future: scraping, APIs, data analysis
]

# Use case: Deep, comprehensive research
# - Multi-source synthesis
# - Trend analysis over time
# - Competitor deep-dives
# - Data gathering and analysis
```

**ContentAgentSDK** (Content Creation):
```python
tools = [
    EMIT_WORK_OUTPUT_TOOL,
    {"type": "web_search_20250305", "name": "web_search"},  # YES - for trending topics
    {"type": "code_execution_20250825", "name": "code_execution"}  # For Skills
]

# Use case: Quick, tactical checks during content creation
# - "What hashtags are trending NOW for this topic?"
# - "What's the latest post from competitor X?"
# - NOT: Deep analysis or multi-source synthesis
```

**Key Distinction**:
- **ResearchAgent**: Deep, comprehensive, multi-source research
- **ContentAgent**: Quick, tactical, real-time checks

**Example Scenarios**:

```python
# Scenario 1: Deep research needed
# User: "Create comprehensive LinkedIn series about AI agent trends"
workflow = ResearchThenContentWorkflow()
result = await workflow.execute(
    topic="AI agent trends",
    platform="linkedin"
)
# ResearchAgent: Deep-dive (30 min research, 10 sources, synthesis)
# ContentAgent: Uses research findings + checks trending hashtags

# Scenario 2: Quick tactical content
# User: "Create Twitter thread about our new feature"
content_agent = ContentAgentSDK(...)
result = await content_agent.create(
    platform="twitter",
    topic="New feature: Real-time collaboration"
)
# ContentAgent: Searches trending hashtags for "collaboration" (5 seconds)
# NO ResearchAgent needed
```

---

#### Specific Example: Social Media Tracking

**Your Question**: "web search for social media tracking subagent that currently resides under research agent"

**Current**: social_listener subagent in ResearchAgent
```python
# ResearchAgent subagents
self.subagents.register(
    SubagentDefinition(
        name="social_listener",
        description="Monitor social media, communities, forums for signals",
        system_prompt=SOCIAL_LISTENER_PROMPT
    )
)
```

**Question**: Should this move to ContentAgent?

**Analysis**:

**If the use case is**:
- ✅ "Monitor Twitter for mentions of our brand over 30 days"
- ✅ "Track competitor sentiment across Reddit, HN, Twitter"
- ✅ "Identify emerging narratives in AI agent discussion"
→ **Keep in ResearchAgent** (this is research/monitoring)

**If the use case is**:
- ✅ "What's trending on Twitter RIGHT NOW for this topic?"
- ✅ "Check latest engagement metrics for competitor's last post"
- ✅ "What hashtags are people using for similar content TODAY?"
→ **ContentAgent can do this directly with web_search tool**

**Recommendation**:
- **social_listener subagent**: Stay in ResearchAgent (long-term monitoring)
- **Trending topic checks**: ContentAgent uses web_search directly (real-time)

---

#### Proposed Agent Responsibilities (After Refactor)

**ResearchAgentSDK** - Information Intelligence
- **Primary Job**: Deep, comprehensive research and analysis
- **Tools**: web_search, web_fetch, memory_adapter
- **Subagents**: web_monitor, competitor_tracker, social_listener, analyst
- **Outputs**: findings, insights, recommendations, trend reports
- **Use Case**: "Research competitor pricing strategies" (30 min, 10 sources)

**ContentAgentSDK** - Creative Production
- **Primary Job**: Create platform-optimized content
- **Tools**: web_search (for trending topics), code_execution (for Skills), memory_adapter
- **Subagents**: None (monolithic for now)
- **Outputs**: content drafts, DOCX, PPTX, PDFs
- **Use Case**: "Create LinkedIn post" (5 min, quick trend check)

**ReportingAgentSDK** - Data Synthesis
- **Primary Job**: Transform data into professional deliverables
- **Tools**: code_execution (for Skills), memory_adapter
- **Subagents**: None
- **Outputs**: PDF reports, XLSX dashboards, PPTX decks
- **Use Case**: "Generate Q4 performance report" (data → visualization)

---

**Answer Summary**:

**Should ContentAgent have web_search?** **YES**
- But for different purpose than ResearchAgent
- ContentAgent: Quick tactical checks (trending hashtags)
- ResearchAgent: Deep comprehensive analysis (trend reports)

**Should social_listener move to ContentAgent?** **NO**
- social_listener = long-term monitoring (ResearchAgent's job)
- Trending topic checks = real-time queries (ContentAgent can do with web_search)

**Architecture**: Tool overlap is OK if use cases differ
- Both agents have web_search tool
- Used differently (deep vs tactical)
- Specialization at workflow level, not tool level

---

## Summary of All Three Answers

### Q1: Data Flow
**Answer**: **Hybrid - both direct passing AND storage**
- Research outputs: Stored in work_outputs table
- Context passing: Direct (in-memory, low latency)
- Substrate absorption: Async (for future reuse)

### Q2: Orchestration Ownership
**Answer**: **New workflows/ module in work-platform**
- Single-agent: agent_orchestration.py (exists)
- Multi-agent: workflows/ module (new)
- Workflow owns: sequencing, context passing, approvals
- Workflow delegates: agent execution, storage, substrate ops

### Q3: Agent Responsibilities
**Answer**: **Give agents tools for their PRIMARY job**
- ResearchAgent: web_search for deep analysis
- ContentAgent: web_search for quick tactical checks
- Tool overlap OK, use cases differ
- Specialization at workflow level

---

## Next Steps

**Before Coding**:
1. ✅ Agree on hybrid data flow pattern
2. ✅ Agree on workflows/ module ownership
3. ✅ Agree on ContentAgent having web_search (tactical)
4. ⏸️ Design approval checkpoint mechanism
5. ⏸️ Design substrate absorption pipeline

**After Agreement**:
1. Refactor ContentAgentSDK (per plan, add web_search)
2. Create workflows/ module structure
3. Implement first workflow (research_then_content)
4. Test end-to-end with real API calls

Ready to discuss any of these points further before proceeding?
