# TP Work Request Staging Pattern - Implementation Guide

## Architecture: TP as "Work Request Roll-Up + Staging Gateway"

### Core Principle

**TP has THREE distinct phases, each with different substrate access patterns:**

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: CHAT (No Substrate)                               │
│ - Pure conversation via Claude SDK session                  │
│ - Requirement collection ("What do you need?")              │
│ - Clarification questions ("Which platform?")               │
│ - Decision point: "Do we have enough to create work?"       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: STAGING (Substrate Queries - ONCE)                │
│ - Load basket substrate context (long-term knowledge)       │
│ - Load reference assets (task-specific resources)           │
│ - Load agent config (agent-specific settings)               │
│ - Create work_request + work_ticket records                 │
│ - Bundle everything into work package                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: DELEGATION (No Substrate - Agent Uses Bundle)     │
│ - Pass complete bundle to specialist agent                  │
│ - Agent executes with pre-loaded context (fast!)            │
│ - Agent emits work_outputs                                  │
│ - TP receives outputs, synthesizes response                 │
└─────────────────────────────────────────────────────────────┘
```

## Two Types of Context - Properly Separated

### Type 1: Long-term Knowledge Base (Substrate Context)

**What**: Persistent knowledge about basket/project
**When**: Loaded during staging phase
**Query**: `GET /baskets/{basket_id}/blocks`

```python
substrate_context = {
    "blocks": [
        {"id": "block_1", "title": "Company mission", "content": "..."},
        {"id": "block_2", "title": "Brand voice guidelines", "content": "..."},
        # ... up to 50 most relevant blocks
    ],
    "documents": [
        {"id": "doc_1", "title": "Past LinkedIn strategy", "content": "..."}
    ],
    "metadata": {
        "total_blocks": 150,
        "last_updated": "2025-11-21T12:00:00Z"
    }
}
```

**Purpose**: Gives agent broad context about what system knows.

### Type 2: Task-Specific Resources (Reference Assets)

**What**: Resources specific to THIS agent and THIS task
**When**: Loaded during staging phase
**Query**: `GET /baskets/{basket_id}/reference-assets?agent_type={agent_type}`

```python
reference_assets = [
    {
        "id": "asset_1",
        "type": "research_template",
        "url": "https://storage/.../template.pdf",
        "signed_url": "https://storage/...?signature=...",
        "permanence": "permanent"
    },
    {
        "id": "asset_2",
        "type": "competitor_list",
        "url": "https://storage/.../competitors.xlsx",
        "signed_url": "https://storage/...?signature=...",
        "permanence": "permanent"
    }
]
```

**Purpose**: Gives agent task-specific tools and templates.

## Implementation Changes

### Change 1: Remove Automatic Memory Loading from TP Chat

**File**: `work-platform/api/src/agents_sdk/thinking_partner_sdk.py`

**Before** (lines 898-913):
```python
async def chat(self, user_message: str, claude_session_id: Optional[str] = None):
    # ...
    # Query memory for context
    context = None
    if self.memory:
        memory_results = await self.memory.query(user_message, limit=5)  # ❌ REMOVE
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

**After**:
```python
async def chat(self, user_message: str, claude_session_id: Optional[str] = None):
    # ...
    # NO memory loading during chat phase
    # TP relies on Claude SDK session for conversation history
    # Substrate context loaded during staging phase (work_orchestration tool)

    full_prompt = user_message  # Simple, no context injection
```

**Rationale**: TP chat should be FAST. SDK session provides conversation memory.

### Change 2: Create Work Bundle Data Structure

**File**: `work-platform/api/src/agents_sdk/work_bundle.py` (NEW)

```python
"""
Work Bundle - Complete context package for specialist agent execution.

Created by TP during staging phase, passed to specialist agents.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class SubstrateContext:
    """Long-term knowledge base context."""
    blocks: List[Dict[str, Any]]
    documents: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class ReferenceAsset:
    """Task-specific resource."""
    id: str
    type: str  # research_template, competitor_list, style_guide, etc.
    url: str
    signed_url: str
    permanence: str  # permanent, temporary


@dataclass
class AgentConfig:
    """Agent-specific configuration."""
    platforms: List[str]  # For content: ["linkedin", "twitter"]
    depth: str  # For research: "quick_scan" | "deep_dive"
    output_format: str  # For reporting: "pdf" | "xlsx"
    custom_params: Dict[str, Any]


@dataclass
class WorkBundle:
    """
    Complete context bundle for specialist agent execution.

    Created by TP during staging phase, contains everything agent needs.
    Agent executes WITHOUT additional substrate queries.
    """
    # Work tracking
    work_request_id: str
    work_ticket_id: str
    basket_id: str
    workspace_id: str
    user_id: str

    # Task definition
    task: str
    agent_type: str  # research, content, reporting
    priority: str  # high, medium, low

    # Pre-loaded context (from staging phase)
    substrate_context: Optional[SubstrateContext] = None
    reference_assets: List[ReferenceAsset] = None
    agent_config: Optional[AgentConfig] = None

    # User requirements (from chat collection)
    user_requirements: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "work_request_id": self.work_request_id,
            "work_ticket_id": self.work_ticket_id,
            "basket_id": self.basket_id,
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "task": self.task,
            "agent_type": self.agent_type,
            "priority": self.priority,
            "substrate_context": {
                "blocks": self.substrate_context.blocks if self.substrate_context else [],
                "documents": self.substrate_context.documents if self.substrate_context else [],
                "metadata": self.substrate_context.metadata if self.substrate_context else {}
            } if self.substrate_context else None,
            "reference_assets": [
                {
                    "id": asset.id,
                    "type": asset.type,
                    "url": asset.url,
                    "signed_url": asset.signed_url,
                    "permanence": asset.permanence
                } for asset in self.reference_assets
            ] if self.reference_assets else [],
            "agent_config": {
                "platforms": self.agent_config.platforms if self.agent_config else [],
                "depth": self.agent_config.depth if self.agent_config else "medium",
                "output_format": self.agent_config.output_format if self.agent_config else "text",
                "custom_params": self.agent_config.custom_params if self.agent_config else {}
            } if self.agent_config else None,
            "user_requirements": self.user_requirements or {}
        }
```

### Change 3: Implement Staging Phase in work_orchestration

**File**: `work-platform/api/src/agents_sdk/thinking_partner_sdk.py`

**Update _execute_work_orchestration method**:

```python
async def _execute_work_orchestration(self, tool_input: Dict[str, Any]) -> str:
    """
    Execute work_orchestration tool - STAGING PHASE.

    This is where substrate queries happen (ONCE):
    1. Load substrate context (long-term knowledge)
    2. Load reference assets (task-specific)
    3. Load agent config (agent settings)
    4. Create work_request + work_ticket
    5. Bundle everything
    6. Delegate to specialist

    Args:
        tool_input: {
            "agent_type": "research" | "content" | "reporting",
            "task": "Description of what to do",
            "priority": "high" | "medium" | "low",
            "user_requirements": {...}  # Collected from chat
        }

    Returns:
        JSON with work outputs
    """
    agent_type = tool_input.get('agent_type')
    task = tool_input.get('task')
    priority = tool_input.get('priority', 'medium')
    user_requirements = tool_input.get('user_requirements', {})

    logger.info(f"STAGING work request: agent={agent_type}, task={task[:100]}")

    try:
        # ================================================================
        # STAGING PHASE - Load ALL context ONCE
        # ================================================================

        # Step 1: Load substrate context (long-term knowledge)
        logger.info("Loading substrate context...")
        substrate_context = await self._load_substrate_context()

        # Step 2: Load reference assets (task-specific)
        logger.info(f"Loading reference assets for {agent_type}...")
        reference_assets = await self._load_reference_assets(agent_type)

        # Step 3: Load agent config
        logger.info(f"Loading agent config for {agent_type}...")
        agent_config = await self._load_agent_config(agent_type)

        # Step 4: Create work request + work ticket
        logger.info("Creating work request and ticket...")
        work_request = await self._create_work_request(task, agent_type, priority)
        work_ticket = await self._create_work_ticket(work_request['id'], agent_type)

        # Step 5: Bundle everything
        work_bundle = WorkBundle(
            work_request_id=work_request['id'],
            work_ticket_id=work_ticket['id'],
            basket_id=self.basket_id,
            workspace_id=self.workspace_id,
            user_id=self.user_id,
            task=task,
            agent_type=agent_type,
            priority=priority,
            substrate_context=substrate_context,
            reference_assets=reference_assets,
            agent_config=agent_config,
            user_requirements=user_requirements
        )

        logger.info(
            f"Work bundle staged: "
            f"{len(substrate_context.blocks) if substrate_context else 0} blocks, "
            f"{len(reference_assets)} assets"
        )

        # ================================================================
        # DELEGATION PHASE - Pass bundle to specialist
        # ================================================================

        # Get or create specialist session (hierarchical)
        specialist_session = await self._get_or_create_specialist_session(agent_type)

        # Create specialist agent with bundle (NO memory adapter!)
        specialist = await self._create_specialist_with_bundle(
            agent_type=agent_type,
            work_bundle=work_bundle,
            session=specialist_session
        )

        # Execute (agent uses pre-loaded bundle, no substrate queries!)
        logger.info(f"Delegating to {agent_type} agent...")
        result = await specialist.execute(work_bundle)

        # Update work ticket status
        await self._update_work_ticket_status(work_ticket['id'], 'completed')

        logger.info(
            f"Work orchestration complete: "
            f"{len(result.get('work_outputs', []))} outputs generated"
        )

        return json.dumps({
            "status": "completed",
            "work_request_id": work_request['id'],
            "work_ticket_id": work_ticket['id'],
            "work_outputs": result.get('work_outputs', []),
            "agent_type": agent_type
        })

    except Exception as e:
        logger.error(f"Work orchestration FAILED: {e}", exc_info=True)
        return json.dumps({
            "status": "error",
            "error": str(e),
            "agent_type": agent_type
        })


async def _load_substrate_context(self) -> Optional[SubstrateContext]:
    """
    Load substrate context (long-term knowledge base).

    Returns:
        SubstrateContext with blocks, documents, metadata
    """
    try:
        from clients.substrate_client import SubstrateClient

        client = SubstrateClient(user_token=self.user_token)

        # Get basket blocks (mature knowledge)
        blocks = client.get_basket_blocks(
            basket_id=self.basket_id,
            states=["ACCEPTED", "LOCKED"],
            limit=50  # Top 50 most relevant
        )

        # TODO: Get documents (compositions)
        # documents = client.get_basket_documents(self.basket_id)
        documents = []

        return SubstrateContext(
            blocks=blocks,
            documents=documents,
            metadata={
                "total_blocks": len(blocks),
                "basket_id": self.basket_id,
                "loaded_at": datetime.utcnow().isoformat()
            }
        )

    except Exception as e:
        logger.warning(f"Failed to load substrate context: {e}")
        return None


async def _load_reference_assets(self, agent_type: str) -> List[ReferenceAsset]:
    """
    Load reference assets for specific agent type.

    Args:
        agent_type: "research" | "content" | "reporting"

    Returns:
        List of ReferenceAsset objects
    """
    try:
        from clients.substrate_client import SubstrateClient

        client = SubstrateClient(user_token=self.user_token)

        # Get agent-scoped assets
        assets_data = client.get_reference_assets(
            basket_id=self.basket_id,
            agent_type=agent_type,
            work_ticket_id=None,  # Only permanent assets
            permanence="permanent"
        )

        return [
            ReferenceAsset(
                id=asset['id'],
                type=asset['type'],
                url=asset['url'],
                signed_url=asset.get('signed_url', asset['url']),
                permanence=asset.get('permanence', 'permanent')
            ) for asset in assets_data
        ]

    except Exception as e:
        logger.warning(f"Failed to load reference assets: {e}")
        return []


async def _load_agent_config(self, agent_type: str) -> Optional[AgentConfig]:
    """
    Load agent configuration from work-platform database.

    Args:
        agent_type: "research" | "content" | "reporting"

    Returns:
        AgentConfig object or None
    """
    try:
        from app.utils.supabase_client import supabase_admin_client

        response = supabase_admin_client.table("project_agents").select(
            "config"
        ).eq("basket_id", self.basket_id).eq(
            "agent_type", agent_type
        ).eq("is_active", True).limit(1).execute()

        if response.data and len(response.data) > 0:
            config_data = response.data[0].get("config", {})
            return AgentConfig(
                platforms=config_data.get("platforms", []),
                depth=config_data.get("depth", "medium"),
                output_format=config_data.get("output_format", "text"),
                custom_params=config_data.get("custom_params", {})
            )

        return None

    except Exception as e:
        logger.warning(f"Failed to load agent config: {e}")
        return None
```

### Change 4: Update Specialist Agents to Accept Bundle

**File**: `work-platform/api/src/agents_sdk/research_agent_sdk.py`

**Before**:
```python
class ResearchAgentSDK:
    def __init__(
        self,
        session: Optional[AgentSession] = None,
        memory: Optional[MemoryProvider] = None  # ❌ Memory adapter
    ):
        self.session = session
        self.memory = memory  # Query substrate during execution
```

**After**:
```python
class ResearchAgentSDK:
    def __init__(
        self,
        session: Optional[AgentSession] = None,
        work_bundle: Optional[WorkBundle] = None  # ✅ Pre-loaded bundle
    ):
        self.session = session
        self.work_bundle = work_bundle  # Complete context, no queries needed!

    async def execute(self, work_bundle: Optional[WorkBundle] = None) -> Dict[str, Any]:
        """
        Execute research work with pre-loaded bundle.

        Args:
            work_bundle: Complete context (substrate + assets + config)

        Returns:
            {work_outputs: [...], status: "completed"}
        """
        bundle = work_bundle or self.work_bundle
        if not bundle:
            raise ValueError("WorkBundle required for execution")

        # Extract pre-loaded context from bundle
        substrate_blocks = bundle.substrate_context.blocks if bundle.substrate_context else []
        reference_assets = bundle.reference_assets or []
        agent_config = bundle.agent_config

        # Build prompt with bundle context (no queries!)
        context_prompt = self._build_context_from_bundle(bundle)

        # Execute research with Claude SDK
        async with ClaudeSDKClient(options=self._options) as client:
            if self.session and self.session.sdk_session_id:
                await client.connect(session_id=self.session.sdk_session_id)
            else:
                await client.connect()

            await client.query(f"""
{context_prompt}

**Task**: {bundle.task}

**Instructions**: Conduct research using provided context and web search.
""")

            # Collect responses and work outputs
            response_text = ""
            work_outputs = []

            async for message in client.receive_response():
                # Process response...
                pass

            return {
                "work_outputs": work_outputs,
                "status": "completed",
                "session_id": client.session_id
            }
```

### Change 5: Remove Memory Adapter from TP Initialization

**File**: `work-platform/api/src/agents_sdk/thinking_partner_sdk.py`

**Before** (lines 291-296):
```python
def __init__(self, ...):
    # ...
    # Create memory adapter using BFF pattern with user token
    self.memory = SubstrateMemoryAdapter(
        basket_id=basket_id,
        workspace_id=workspace_id,
        user_token=user_token
    )
```

**After**:
```python
def __init__(self, ...):
    # ...
    # NO memory adapter for TP chat
    # Substrate queries happen during staging phase (work_orchestration tool)
    self.memory = None
```

## System Prompt Changes

**File**: `work-platform/api/src/agents_sdk/thinking_partner_sdk.py`

**Update lines 105-127**:

**Before**:
```
When user makes a request:
1. **Understand Intent**: What does user want?
2. **Query Context**: What do we already know? (memory.query)
3. **Check Work State**: Any relevant ongoing/past work? (infra_reader)
4. **Decide Action** (KEY DECISION):
```

**After**:
```
When user makes a request:
1. **Understand Intent**: What does user want?
2. **Collect Requirements**: Do you have all necessary information?
   - Platform? (LinkedIn, Twitter, Blog)
   - Topic/Focus? (AI agents, enterprise adoption)
   - Style/Tone? (Professional, casual, technical)
   - Timeline? (Urgent, normal)
3. **Decide Action** (KEY DECISION):
   - **Need more info?** → Ask clarifying questions (stay in chat mode)
   - **Have complete requirements?** → Call work_orchestration tool (staging phase)
   - **Simple question?** → Check existing work_outputs via infra_reader (database query)
4. **Stage & Delegate**: When ready, call work_orchestration
   - I will load all necessary context (substrate + assets + config)
   - I will create work_request and work_ticket
   - I will bundle everything and delegate to specialist
   - Specialist will execute with complete bundle (fast!)
5. **Synthesize & Respond**: Present work outputs to user
```

## Benefits of This Pattern

### 1. **Performance** ✅
- TP chat: ZERO substrate queries → instant responses
- Staging: 3 queries (substrate + assets + config) → reasonable (~1-2 seconds)
- Agent execution: ZERO substrate queries → fast execution

### 2. **Clarity** ✅
- Chat phase: Conversation only
- Staging phase: Context assembly
- Delegation phase: Execution with bundle
- Clear responsibility boundaries

### 3. **Efficiency** ✅
- No duplicate queries (agent doesn't re-query what TP already loaded)
- No wasted queries (no substrate call for "hello")
- Amortized cost (3 queries per work request, not per message)

### 4. **Determinism** ✅
- Agent receives complete bundle (same input → same execution)
- TP controls what agent sees (security boundary)
- Reproducible results (bundle can be logged/audited)

### 5. **Scalability** ✅
- TP chat is stateless (SDK session only)
- Substrate queries happen at controlled boundary (staging)
- Work bundles can be queued, cached, replayed

## Migration Path

### Step 1: Implement WorkBundle Data Structure
- Create `work_bundle.py`
- Define SubstrateContext, ReferenceAsset, AgentConfig, WorkBundle

### Step 2: Remove Memory from TP Chat
- Set `self.memory = None` in TP init
- Remove lines 901-913 (automatic memory query)

### Step 3: Implement Staging Methods
- `_load_substrate_context()`
- `_load_reference_assets(agent_type)`
- `_load_agent_config(agent_type)`

### Step 4: Update work_orchestration Tool
- Implement staging phase (load context)
- Create WorkBundle
- Delegate with bundle

### Step 5: Update Specialist Agents
- Accept `work_bundle` parameter
- Use bundle instead of memory adapter
- Remove substrate queries from agent code

### Step 6: Test End-to-End
- TP chat (should be fast, no substrate)
- Work creation (should stage context)
- Agent execution (should use bundle)
- Verify no duplicate queries

### Step 7: Update System Prompt
- Remove "query context" step
- Add "collect requirements" guidance
- Clarify staging boundary

## Next Steps

Ready to implement? I recommend:

1. **Start with Step 1-2** (remove memory from chat) - immediate performance win
2. **Implement Step 3** (staging methods) - enables work orchestration
3. **Test with one specialist** (Research) - validate pattern
4. **Roll out to others** (Content, Reporting) - scale pattern

Want me to implement Steps 1-3 now?
