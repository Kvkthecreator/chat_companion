# Agent Providers

**YARNNN Provider Implementations for Agent SDK**

**Version**: 4.0
**Date**: 2025-10-31
**Status**: ✅ Canonical
**Layer**: Integration
**Category**: Feature Specification

---

## 🎯 Overview

YARNNN implements three provider interfaces from the Agent SDK: Memory, Governance, and Tasks. These providers enable agents to access YARNNN's context, submit work for approval, and discover tasks.

**Key Concepts**:
- Providers implement generic interfaces defined by Agent SDK
- YARNNN providers call YARNNN Core APIs (no direct database access)
- Providers are stateless (session state managed by Agent SDK)
- Providers handle authentication via API tokens

---

## 🧠 YarnnnMemoryProvider

**Purpose**: Enable agents to retrieve context from YARNNN substrate.

**File**: `api/src/app/agent_providers/yarnnn_memory.py`

### Interface

```typescript
interface MemoryProvider {
  retrieveContext(
    query: string,
    sessionMetadata: SessionMetadata
  ): Promise<ContextItem[]>

  storeMemory(
    content: string,
    metadata: Record<string, any>
  ): Promise<StorageResult>
}

interface SessionMetadata {
  workspace_id: UUID
  basket_id: UUID
  work_session_id?: UUID
}

interface ContextItem {
  content: string
  source_id: UUID
  relevance: number
  metadata: Record<string, any>
}
```

### Implementation

```python
# api/src/app/agent_providers/yarnnn_memory.py

class YarnnnMemoryProvider(MemoryProvider):
    """
    YARNNN implementation of Memory Provider
    """

    def __init__(self, api_client: ApiClient, auth_token: str):
        self.api_client = api_client
        self.auth_token = auth_token

    async def retrieve_context(
        self,
        query: str,
        session_metadata: SessionMetadata
    ) -> List[ContextItem]:
        """
        Semantic search across substrate blocks
        """

        response = await self.api_client.post(
            '/substrate/semantic/search',
            headers={'Authorization': f'Bearer {self.auth_token}'},
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
                source_id=UUID(r['block']['id']),
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
        YARNNN does not support direct storage (governance required)
        """

        raise NotImplementedError(
            "Direct memory storage not supported in YARNNN. "
            "Use YarnnnGovernanceProvider.submit_artifact() to create "
            "work artifacts that go through approval before becoming blocks."
        )

    async def get_recent_memories(
        self,
        workspace_id: UUID,
        basket_id: UUID,
        limit: int = 10
    ) -> List[ContextItem]:
        """
        Get recently created/updated blocks
        """

        response = await self.api_client.get(
            '/substrate/blocks',
            headers={'Authorization': f'Bearer {self.auth_token}'},
            params={
                'workspace_id': str(workspace_id),
                'basket_id': str(basket_id),
                'state': 'ACCEPTED',
                'limit': limit,
                'sort': '-created_at'
            }
        )

        blocks = response.json()['blocks']

        return [
            ContextItem(
                content=b['content']['text'],
                source_id=UUID(b['id']),
                relevance=1.0,  # Recent, not similarity-based
                metadata=b['metadata']
            )
            for b in blocks
        ]
```

### Usage Example

```python
# Initialize provider
memory_provider = YarnnnMemoryProvider(
    api_client=httpx.AsyncClient(),
    auth_token=os.environ['YARNNN_API_TOKEN']
)

# Retrieve context during agent work
context = await memory_provider.retrieve_context(
    query="pricing strategies for SaaS products",
    session_metadata={
        'workspace_id': 'ws-123',
        'basket_id': 'basket-456',
        'work_session_id': 'session-789'
    }
)

# Use context for reasoning
for item in context:
    print(f"[Relevance: {item.relevance:.2f}] {item.content}")
```

---

## ⚖️ YarnnnGovernanceProvider

**Purpose**: Enable agents to submit work artifacts for approval.

**File**: `api/src/app/agent_providers/yarnnn_governance.py`

### Interface

```typescript
interface GovernanceProvider {
  submitArtifact(
    sessionId: UUID,
    artifactType: string,
    content: Record<string, any>,
    confidence: number,
    reasoning: string,
    sourceContextIds: UUID[]
  ): Promise<UUID>

  markWorkComplete(sessionId: UUID): Promise<void>

  getIterationFeedback(
    sessionId: UUID,
    iterationId: UUID
  ): Promise<IterationFeedback>
}
```

### Implementation

```python
# api/src/app/agent_providers/yarnnn_governance.py

class YarnnnGovernanceProvider(GovernanceProvider):
    """
    YARNNN implementation of Governance Provider
    """

    def __init__(self, api_client: ApiClient, auth_token: str):
        self.api_client = api_client
        self.auth_token = auth_token

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
        Submit work artifact to YARNNN governance
        """

        response = await self.api_client.post(
            '/work/artifacts',
            headers={'Authorization': f'Bearer {self.auth_token}'},
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
        Mark work session complete (ready for review)
        """

        await self.api_client.patch(
            f'/work/sessions/{session_id}/status',
            headers={'Authorization': f'Bearer {self.auth_token}'},
            json={'status': 'pending_review'}
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
            f'/work/iterations/{iteration_id}',
            headers={'Authorization': f'Bearer {self.auth_token}'}
        )

        iteration = response.json()['iteration']

        return IterationFeedback(
            iteration_number=iteration['iteration_number'],
            user_feedback=iteration['user_feedback_text'],
            changes_requested=iteration['changes_requested']
        )

    async def check_work_status(
        self,
        session_id: UUID
    ) -> WorkStatus:
        """
        Check if work approved, rejected, or iteration requested
        """

        response = await self.api_client.get(
            f'/work/sessions/{session_id}',
            headers={'Authorization': f'Bearer {self.auth_token}'}
        )

        session = response.json()['session']

        return WorkStatus(
            status=session['status'],
            approved=session['status'] == 'completed_approved',
            rejected=session['status'] == 'rejected',
            iteration_requested=session['status'] == 'iteration_requested'
        )
```

### Usage Example

```python
# Initialize provider
governance_provider = YarnnnGovernanceProvider(
    api_client=httpx.AsyncClient(),
    auth_token=os.environ['YARNNN_API_TOKEN']
)

# Submit artifacts during work
artifact_id_1 = await governance_provider.submit_artifact(
    session_id=session_id,
    artifact_type='block_proposal',
    content={
        'block_content': {
            'text': 'Freemium model: Free tier with 10GB storage...',
            'entities': ['freemium', 'pricing', 'storage']
        },
        'block_type': 'research_finding'
    },
    confidence=0.92,
    reasoning='Pricing model verified from multiple SaaS companies',
    source_context_ids=[context_block_1.source_id, context_block_2.source_id]
)

# Mark work complete
await governance_provider.mark_work_complete(session_id)

# Later: Check if user approved
status = await governance_provider.check_work_status(session_id)

if status.approved:
    print("Work approved! Artifacts applied to substrate.")
elif status.iteration_requested:
    feedback = await governance_provider.get_iteration_feedback(
        session_id, status.iteration_id
    )
    print(f"Revision requested: {feedback.user_feedback}")
```

---

## 📋 YarnnnTasksProvider

**Purpose**: Enable agents to discover and claim tasks.

**File**: `api/src/app/agent_providers/yarnnn_tasks.py`

### Interface

```typescript
interface TasksProvider {
  getAvailableTasks(
    workspaceId: UUID,
    agentCapabilities: string[]
  ): Promise<Task[]>

  claimTask(
    taskId: UUID,
    agentId: string
  ): Promise<WorkSession>

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
  priority?: number
  created_at: ISO8601
}
```

### Implementation

```python
# api/src/app/agent_providers/yarnnn_tasks.py

class YarnnnTasksProvider(TasksProvider):
    """
    YARNNN implementation of Tasks Provider
    """

    def __init__(self, api_client: ApiClient, auth_token: str):
        self.api_client = api_client
        self.auth_token = auth_token

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
            headers={'Authorization': f'Bearer {self.auth_token}'},
            params={
                'workspace_id': str(workspace_id),
                'status': 'initialized',
                'task_type': ','.join(agent_capabilities)
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
                priority=s.get('priority', 0),
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
            headers={'Authorization': f'Bearer {self.auth_token}'},
            json={
                'status': 'in_progress',
                'executed_by_agent_id': agent_id,
                'agent_session_id': str(uuid4())
            }
        )

        return response.json()['session']

    async def update_progress(
        self,
        session_id: UUID,
        progress: ProgressUpdate
    ) -> None:
        """
        Update work session with progress
        """

        await self.api_client.post(
            f'/work/sessions/{session_id}/reasoning',
            headers={'Authorization': f'Bearer {self.auth_token}'},
            json={
                'reasoning': progress.message,
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    async def poll_for_tasks(
        self,
        workspace_id: UUID,
        agent_capabilities: List[str],
        interval_seconds: int = 30
    ) -> AsyncGenerator[Task, None]:
        """
        Continuously poll for new tasks
        """

        while True:
            tasks = await self.get_available_tasks(
                workspace_id, agent_capabilities
            )

            for task in tasks:
                yield task

            await asyncio.sleep(interval_seconds)
```

### Usage Example

```python
# Initialize provider
tasks_provider = YarnnnTasksProvider(
    api_client=httpx.AsyncClient(),
    auth_token=os.environ['YARNNN_API_TOKEN']
)

# Poll for tasks
async for task in tasks_provider.poll_for_tasks(
    workspace_id='ws-123',
    agent_capabilities=['research', 'synthesis', 'analysis'],
    interval_seconds=30
):
    print(f"New task: {task.task_intent}")

    # Claim task
    session = await tasks_provider.claim_task(
        task_id=task.id,
        agent_id='claude-opus-20250115'
    )

    # Execute task
    await execute_task(session, tasks_provider, memory_provider, governance_provider)
```

---

## 🔧 Provider Factory

**File**: `api/src/app/agent_providers/factory.py`

```python
# api/src/app/agent_providers/factory.py

class YarnnnProviderFactory:
    """
    Factory for creating YARNNN providers
    """

    @staticmethod
    def create_providers(
        api_base_url: str,
        auth_token: str
    ) -> dict:
        """
        Create all YARNNN providers
        """

        api_client = httpx.AsyncClient(base_url=api_base_url)

        return {
            'memory': YarnnnMemoryProvider(api_client, auth_token),
            'governance': YarnnnGovernanceProvider(api_client, auth_token),
            'tasks': YarnnnTasksProvider(api_client, auth_token)
        }

    @staticmethod
    def create_from_env() -> dict:
        """
        Create providers from environment variables
        """

        api_base_url = os.environ.get(
            'YARNNN_API_BASE_URL',
            'https://api.yarnnn.com'
        )

        auth_token = os.environ['YARNNN_API_TOKEN']

        return YarnnnProviderFactory.create_providers(
            api_base_url, auth_token
        )
```

### Usage

```python
# In Agent SDK session
from yarnnn_providers import YarnnnProviderFactory

providers = YarnnnProviderFactory.create_from_env()

agent_session = await agent_sdk.create_session(
    agent_id='claude-opus-20250115',
    providers=providers
)
```

---

## 🔐 Authentication

### API Token Generation

```python
# Generate API token for agent
async def create_agent_api_token(
    workspace_id: UUID,
    agent_id: str,
    created_by_user_id: UUID
) -> str:
    """
    Create scoped API token for agent
    """

    token = await db.api_tokens.create(
        workspace_id=workspace_id,
        token_type='agent',
        agent_id=agent_id,
        scopes=[
            'work:read',
            'work:write',
            'substrate:read',
            'governance:submit'
        ],
        created_by=created_by_user_id,
        expires_at=datetime.utcnow() + timedelta(days=365)
    )

    return token.token_value
```

### Token Scopes

| Scope | Permissions |
|-------|-------------|
| `work:read` | Read work sessions, artifacts |
| `work:write` | Create artifacts, update progress |
| `substrate:read` | Read blocks, search semantically |
| `governance:submit` | Submit artifacts for review |

---

## 📊 Provider Metrics

```typescript
interface ProviderMetrics {
  provider_type: 'memory' | 'governance' | 'tasks'

  // API calls
  totalCalls: number
  successfulCalls: number
  failedCalls: number
  avgLatencyMs: number

  // Memory provider
  totalContextRetrievals?: number
  avgRelevanceScore?: number

  // Governance provider
  totalArtifactsSubmitted?: number
  artifactsPerSession?: number

  // Tasks provider
  totalTasksClaimed?: number
  tasksCompleted?: number
}
```

---

## 📎 See Also

- [AGENT_SDK_INTEGRATION.md](../work-management/AGENT_SDK_INTEGRATION.md) - Complete integration spec
- [WORK_SESSION_LIFECYCLE.md](../work-management/WORK_SESSION_LIFECYCLE.md) - Session states
- [ARTIFACT_TYPES_AND_HANDLING.md](../work-management/ARTIFACT_TYPES_AND_HANDLING.md) - Artifact types
- [claude-agentsdk-yarnnn](https://github.com/Kvkthecreator/claude-agentsdk-yarnnn) - Agent SDK repository

---

**3 providers. Memory, Governance, Tasks. YARNNN-specific implementations of generic interfaces.**
