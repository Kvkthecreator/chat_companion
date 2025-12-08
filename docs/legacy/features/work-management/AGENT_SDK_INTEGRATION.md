# Agent SDK Integration

**How claude-agentsdk-yarnnn Integrates with YARNNN Core**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: 2 (Work Orchestration) + Agent SDK
**Category**: Feature Specification

---

## 🎯 Overview

The [claude-agentsdk-yarnnn](https://github.com/Kvkthecreator/claude-agentsdk-yarnnn) provides a generic agent framework with YARNNN as one integration. This document specifies how the Agent SDK integrates with YARNNN Core for work orchestration, context management, and governance.

**Key Principles**:
- **Separation of Concerns**: Agent SDK handles execution, YARNNN Core handles work management + context
- **Session Linking**: Two session concepts linked via metadata, not tightly coupled
- **Provider Pattern**: YARNNN implements generic provider interfaces (Memory, Governance, Tasks)

---

## 🏗️ Architecture Overview

### Two-Session Model

```
┌──────────────────────────────────────────────┐
│ Agent SDK Session (Technical Execution)      │
│ - Claude API conversations                   │
│ - Tool calls                                 │
│ - Error handling                             │
│ - Session state management                   │
└────────────┬─────────────────────────────────┘
             │
             │ Linked via agent_session_id
             │
             ▼
┌──────────────────────────────────────────────┐
│ YARNNN Work Session (Business Workflow)      │
│ - Task intent                                │
│ - Artifacts awaiting approval                │
│ - Governance checkpoints                     │
│ - Substrate mutations                        │
└──────────────────────────────────────────────┘
```

### Provider Architecture

```
┌─────────────────────────────────────────────────┐
│ Agent SDK Core                                   │
│ - Generic provider interfaces                    │
│ - Session management                             │
│ - Execution loop                                 │
└───────────┬─────────────────────────────────────┘
            │
            │ Uses providers
            ▼
┌────────────────────────────────────────────────┐
│ YARNNN Providers (Concrete Implementations)    │
│ - YarnnnMemoryProvider                         │
│ - YarnnnGovernanceProvider                     │
│ - YarnnnTasksProvider                          │
└────────────────────────────────────────────────┘
            │
            │ Calls YARNNN Core APIs
            ▼
┌────────────────────────────────────────────────┐
│ YARNNN Core (FastAPI Backend)                 │
│ - Work orchestration                           │
│ - Substrate management                         │
│ - Unified governance                           │
└────────────────────────────────────────────────┘
```

---

## 🔌 Provider Interfaces

### 1. Memory Provider (YarnnnMemoryProvider)

**Purpose**: Enable agent to retrieve context from YARNNN substrate.

**Interface**:
```typescript
interface MemoryProvider {
  /**
   * Retrieve relevant context for agent reasoning
   */
  retrieveContext(
    query: string,
    sessionMetadata: SessionMetadata
  ): Promise<ContextItem[]>

  /**
   * Store memory (note: in YARNNN, this goes through governance)
   */
  storeMemory(
    content: string,
    metadata: Record<string, any>
  ): Promise<StorageResult>
}

interface ContextItem {
  content: string
  source_id: UUID                 // Block ID
  relevance: number               // Similarity score
  metadata: Record<string, any>
}

interface SessionMetadata {
  workspace_id: UUID
  basket_id: UUID
  work_session_id?: UUID
}
```

**YARNNN Implementation**:
```python
# api/src/app/agent_providers/yarnnn_memory.py

class YarnnnMemoryProvider(MemoryProvider):
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client

    async def retrieve_context(
        self,
        query: str,
        session_metadata: SessionMetadata
    ) -> List[ContextItem]:
        """
        Semantic search across substrate blocks
        """

        # Call YARNNN semantic search API
        response = await self.api_client.post(
            '/substrate/semantic/search',
            json={
                'workspace_id': session_metadata['workspace_id'],
                'basket_id': session_metadata.get('basket_id'),
                'query_text': query,
                'limit': 10,
                'min_similarity': 0.7
            }
        )

        results = response.json()['results']

        return [
            ContextItem(
                content=r['block']['content']['text'],
                source_id=r['block']['id'],
                relevance=r['similarity'],
                metadata=r['block']['metadata']
            )
            for r in results
        ]

    async def store_memory(
        self,
        content: str,
        metadata: dict
    ) -> StorageResult:
        """
        Note: In YARNNN, storage goes through governance
        Agent must create work artifact instead of direct storage
        """

        raise NotImplementedError(
            "Direct storage not supported in YARNNN. "
            "Use YarnnnGovernanceProvider.submit_artifact() instead."
        )
```

**Usage Example**:
```python
# Agent retrieves context during work session
memory_provider = YarnnnMemoryProvider(api_client)

context = await memory_provider.retrieve_context(
    query="AI memory competitors pricing",
    session_metadata={
        'workspace_id': 'ws-123',
        'basket_id': 'basket-456',
        'work_session_id': 'session-789'
    }
)

# Agent uses context for reasoning
for item in context:
    print(f"Relevant block: {item.content} (relevance: {item.relevance})")
```

---

### 2. Governance Provider (YarnnnGovernanceProvider)

**Purpose**: Enable agent to submit work artifacts for approval.

**Interface**:
```typescript
interface GovernanceProvider {
  /**
   * Submit work artifact for review
   */
  submitArtifact(
    sessionId: UUID,
    artifactType: string,
    content: Record<string, any>,
    confidence: number,
    reasoning: string,
    sourceContextIds: UUID[]
  ): Promise<UUID>

  /**
   * Mark work session complete
   */
  markWorkComplete(sessionId: UUID): Promise<void>

  /**
   * Get iteration feedback (if user requested changes)
   */
  getIterationFeedback(
    sessionId: UUID,
    iterationId: UUID
  ): Promise<IterationFeedback>
}
```

**YARNNN Implementation**:
```python
# api/src/app/agent_providers/yarnnn_governance.py

class YarnnnGovernanceProvider(GovernanceProvider):
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client

    async def submit_artifact(
        self,
        session_id: UUID,
        artifact_type: str,
        content: dict,
        confidence: float,
        reasoning: str,
        source_context_ids: List[UUID]
    ) -> UUID:
        """
        Submit work artifact to YARNNN governance system
        """

        # Call YARNNN work artifacts API
        response = await self.api_client.post(
            '/work/artifacts',
            json={
                'work_session_id': str(session_id),
                'artifact_type': artifact_type,
                'content': content,
                'agent_confidence': confidence,
                'agent_reasoning': reasoning,
                'source_context_ids': [str(id) for id in source_context_ids]
            }
        )

        artifact = response.json()['artifact']
        return UUID(artifact['id'])

    async def mark_work_complete(
        self,
        session_id: UUID
    ) -> None:
        """
        Mark work session as complete (ready for review)
        """

        await self.api_client.patch(
            f'/work/sessions/{session_id}/status',
            json={
                'status': 'pending_review'
            }
        )

    async def get_iteration_feedback(
        self,
        session_id: UUID,
        iteration_id: UUID
    ) -> IterationFeedback:
        """
        Get user feedback for iteration
        """

        response = await self.api_client.get(
            f'/work/iterations/{iteration_id}'
        )

        iteration = response.json()['iteration']

        return IterationFeedback(
            iteration_number=iteration['iteration_number'],
            user_feedback=iteration['user_feedback_text'],
            changes_requested=iteration['changes_requested']
        )
```

**Usage Example**:
```python
# Agent submits artifacts during work
governance_provider = YarnnnGovernanceProvider(api_client)

# Artifact 1: Block proposal
artifact_id_1 = await governance_provider.submit_artifact(
    session_id=session_id,
    artifact_type='block_proposal',
    content={
        'block_content': {
            'text': 'Mem charges $8/month for individuals...',
            'entities': ['Mem', 'pricing']
        },
        'block_type': 'research_finding'
    },
    confidence=0.95,
    reasoning='Verified from official website',
    source_context_ids=[]
)

# Artifact 2: Document creation
artifact_id_2 = await governance_provider.submit_artifact(
    session_id=session_id,
    artifact_type='document_creation',
    content={
        'title': 'Competitor Analysis',
        'document_type': 'research_report',
        'content_blocks': [...]
    },
    confidence=0.88,
    reasoning='Synthesized from research findings',
    source_context_ids=[artifact_id_1]
)

# Mark work complete
await governance_provider.mark_work_complete(session_id)
```

---

### 3. Tasks Provider (YarnnnTasksProvider)

**Purpose**: Enable agent to discover and claim tasks from YARNNN work queue.

**Interface**:
```typescript
interface TasksProvider {
  /**
   * Get available tasks for agent
   */
  getAvailableTasks(
    workspaceId: UUID,
    agentCapabilities: string[]
  ): Promise<Task[]>

  /**
   * Claim task for execution
   */
  claimTask(taskId: UUID, agentId: string): Promise<WorkSession>

  /**
   * Update task progress
   */
  updateProgress(
    sessionId: UUID,
    progress: ProgressUpdate
  ): Promise<void>
}

interface Task {
  id: UUID
  workspace_id: UUID
  basket_id: UUID
  task_intent: string
  task_type: string
  task_document_id?: UUID
  priority?: number
  created_at: ISO8601
}
```

**YARNNN Implementation**:
```python
# api/src/app/agent_providers/yarnnn_tasks.py

class YarnnnTasksProvider(TasksProvider):
    def __init__(self, api_client: ApiClient):
        self.api_client = api_client

    async def get_available_tasks(
        self,
        workspace_id: UUID,
        agent_capabilities: List[str]
    ) -> List[Task]:
        """
        Get work sessions awaiting agent execution
        """

        response = await self.api_client.get(
            '/work/sessions',
            params={
                'workspace_id': str(workspace_id),
                'status': 'initialized',
                'task_type': ','.join(agent_capabilities)  # Filter by capabilities
            }
        )

        sessions = response.json()['sessions']

        return [
            Task(
                id=UUID(s['id']),
                workspace_id=UUID(s['workspace_id']),
                basket_id=UUID(s['basket_id']),
                task_intent=s['task_intent'],
                task_type=s['task_type'],
                task_document_id=UUID(s['task_document_id']) if s.get('task_document_id') else None,
                priority=s.get('priority'),
                created_at=s['created_at']
            )
            for s in sessions
        ]

    async def claim_task(
        self,
        task_id: UUID,
        agent_id: str
    ) -> WorkSession:
        """
        Claim task and start execution
        """

        response = await self.api_client.patch(
            f'/work/sessions/{task_id}/status',
            json={
                'status': 'in_progress',
                'executed_by_agent_id': agent_id,
                'agent_session_id': str(uuid4())  # Link Agent SDK session
            }
        )

        return response.json()['session']

    async def update_progress(
        self,
        session_id: UUID,
        progress: ProgressUpdate
    ) -> None:
        """
        Update work session with progress info
        """

        await self.api_client.post(
            f'/work/sessions/{session_id}/reasoning',
            json={
                'reasoning': progress.message,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
```

**Usage Example**:
```python
# Agent polls for tasks
tasks_provider = YarnnnTasksProvider(api_client)

tasks = await tasks_provider.get_available_tasks(
    workspace_id='ws-123',
    agent_capabilities=['research', 'synthesis', 'analysis']
)

if tasks:
    task = tasks[0]

    # Claim task
    session = await tasks_provider.claim_task(
        task_id=task.id,
        agent_id='claude-opus-20250115'
    )

    # Execute work...
    await tasks_provider.update_progress(
        session_id=session['id'],
        progress=ProgressUpdate(
            message='Starting competitor research...',
            percentage=10
        )
    )
```

---

## 🔗 Session Linking

### Bidirectional Link

```typescript
// Agent SDK Session
interface AgentSDKSession {
  id: UUID
  agent_id: string
  conversation_history: Message[]
  tool_calls: ToolCall[]

  // Link to YARNNN
  yarnnn_work_session_id?: UUID
  yarnnn_workspace_id?: UUID
}

// YARNNN Work Session
interface WorkSession {
  id: UUID
  workspace_id: UUID
  task_intent: string
  artifacts: WorkArtifact[]

  // Link to Agent SDK
  agent_session_id?: string       // Agent SDK session ID
  executed_by_agent_id?: string   // Agent identifier
}
```

### Creating Linked Sessions

```python
# Agent SDK creates session first
agent_session = await agent_sdk.create_session(
    agent_id='claude-opus-20250115',
    config={...}
)

# YARNNN work session links to Agent SDK
work_session = await yarnnn_client.post('/work/sessions', json={
    'workspace_id': 'ws-123',
    'basket_id': 'basket-456',
    'task_intent': 'Research competitors',
    'executed_by_agent_id': agent_session.agent_id,
    'agent_session_id': str(agent_session.id)  # Link here
})

# Agent SDK updates with YARNNN link
await agent_sdk.update_session(
    agent_session.id,
    metadata={
        'yarnnn_work_session_id': work_session['id'],
        'yarnnn_workspace_id': work_session['workspace_id']
    }
)
```

### Cross-Session Debugging

Session linking enables cross-system debugging:

```python
# Given YARNNN work session, find Agent SDK session
work_session = await db.work_sessions.get(session_id)
agent_session_id = work_session.agent_session_id

# Fetch Agent SDK session for debugging
agent_session = await agent_sdk.get_session(agent_session_id)

# See full Claude API conversation history
print(agent_session.conversation_history)
print(agent_session.tool_calls)

# Given Agent SDK session, find YARNNN work session
yarnnn_session_id = agent_session.metadata['yarnnn_work_session_id']
yarnnn_session = await yarnnn_client.get(f'/work/sessions/{yarnnn_session_id}')

# See artifacts, governance decisions
print(yarnnn_session['artifacts'])
print(yarnnn_session['status'])
```

---

## 🔄 Complete Integration Flow

### End-to-End Example

```python
# 1. User creates task in YARNNN
work_session = await yarnnn_client.post('/work/sessions', json={
    'workspace_id': 'ws-123',
    'basket_id': 'basket-456',
    'task_intent': 'Research AI memory competitors',
    'task_type': 'research'
})

session_id = work_session['id']

# 2. Agent SDK polls for tasks
tasks_provider = YarnnnTasksProvider(yarnnn_client)
tasks = await tasks_provider.get_available_tasks('ws-123', ['research'])

# 3. Agent SDK claims task
session = await tasks_provider.claim_task(
    task_id=UUID(tasks[0].id),
    agent_id='claude-opus-20250115'
)

# 4. Agent SDK creates its own session
agent_session = await agent_sdk.create_session(
    agent_id='claude-opus-20250115',
    providers={
        'memory': YarnnnMemoryProvider(yarnnn_client),
        'governance': YarnnnGovernanceProvider(yarnnn_client),
        'tasks': tasks_provider
    },
    metadata={
        'yarnnn_work_session_id': session_id
    }
)

# 5. Agent executes work
# 5a. Retrieve context
memory_provider = agent_session.providers['memory']
context = await memory_provider.retrieve_context(
    query='AI memory competitors',
    session_metadata={
        'workspace_id': 'ws-123',
        'basket_id': 'basket-456'
    }
)

# 5b. Perform research (external tools, web search, etc.)
research_results = await agent_sdk.run_tools([...])

# 5c. Submit artifacts
governance_provider = agent_session.providers['governance']
await governance_provider.submit_artifact(
    session_id=session_id,
    artifact_type='block_proposal',
    content={'block_content': {'text': '...'}},
    confidence=0.95,
    reasoning='...',
    source_context_ids=[]
)

# 5d. Mark complete
await governance_provider.mark_work_complete(session_id)

# 6. User reviews work in YARNNN UI
# (User approves/rejects via YARNNN governance layer)

# 7. If approved → Artifacts applied to substrate
# If iteration requested → Agent SDK notified

# 8. Agent SDK handles iteration (if needed)
iteration = await governance_provider.get_iteration_feedback(
    session_id, iteration_id
)

# Agent revises work based on feedback
# ... (back to step 5b)
```

---

## 📊 Integration Patterns

### Pattern 1: Long-Running Agents

```python
# Agent continuously polls for tasks
while True:
    tasks = await tasks_provider.get_available_tasks(
        workspace_id='ws-123',
        agent_capabilities=['research', 'synthesis']
    )

    if tasks:
        task = tasks[0]
        await execute_task(task)

    await asyncio.sleep(30)  # Poll every 30 seconds
```

### Pattern 2: On-Demand Execution

```python
# Single task execution (e.g., triggered by webhook)
task = await get_specific_task(task_id)
await execute_task(task)
```

### Pattern 3: Multi-Agent Orchestration

```python
# Task decomposition across multiple agents
main_task = await create_work_session('Research and synthesize')

# Create subtasks
subtask_1 = await create_work_session('Research competitors')
subtask_2 = await create_work_session('Synthesize findings')

# Different agents claim different subtasks
agent_1 = await claim_task(subtask_1.id, 'research-specialist')
agent_2 = await claim_task(subtask_2.id, 'synthesis-specialist')
```

---

## 📎 See Also

- [WORK_SESSION_LIFECYCLE.md](./WORK_SESSION_LIFECYCLE.md) - Session states
- [ARTIFACT_TYPES_AND_HANDLING.md](./ARTIFACT_TYPES_AND_HANDLING.md) - Artifact specs
- [claude-agentsdk-yarnnn](https://github.com/Kvkthecreator/claude-agentsdk-yarnnn) - Agent SDK repository
- [YARNNN_UNIFIED_GOVERNANCE.md](../../architecture/YARNNN_UNIFIED_GOVERNANCE.md) - Governance layer

---

**Separation of concerns. Session linking. Provider pattern. Agent SDK + YARNNN Core integrated.**
