# Claude Agent SDK: MCP Tools with Context Injection Pattern

**Last Updated**: 2025-11-20
**Status**: Production (All specialist agents migrated)
**SDK Version**: claude-agent-sdk >= 0.1.8

---

## Table of Contents

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [The Solution](#the-solution)
4. [Implementation Pattern](#implementation-pattern)
5. [Examples](#examples)
6. [Architecture](#architecture)
7. [Testing](#testing)

---

## Overview

This document describes the **official pattern** for creating stateful MCP tools in Claude Agent SDK where tools need access to agent context (basket_id, work_ticket_id, user_id, etc.).

**Key Pattern**: Factory with Closure

The official Claude Agent SDK (v0.1.8+) **does NOT** support a `tools` parameter on `ClaudeAgentOptions`. Instead, custom tools must be:
1. Created with `@tool` decorator from `claude_agent_sdk`
2. Packaged via `create_sdk_mcp_server()`
3. Registered via `mcp_servers` parameter
4. Referenced in `allowed_tools` list

**Context Injection**: Per official SDK documentation, use **"close over context in tool definitions"** - create a factory function that generates tools with context baked in via closure.

---

## The Problem

### Legacy Pattern (BROKEN in SDK v0.1.8+)

```python
from yarnnn_agents.tools import EMIT_WORK_OUTPUT_TOOL

EMIT_WORK_OUTPUT_TOOL = {
    "name": "emit_work_output",
    "description": "...",
    "input_schema": {...}
}

# ❌ BROKEN: ClaudeAgentOptions has no 'tools' parameter!
options = ClaudeAgentOptions(
    model="claude-sonnet-4-5",
    tools=[EMIT_WORK_OUTPUT_TOOL]  # ERROR: unexpected keyword argument 'tools'
)
```

**Why This Fails**:
- `ClaudeAgentOptions` dataclass has no `tools` parameter in SDK v0.1.8+
- Dict-based tool definitions are legacy pattern from raw Anthropic API
- SDK requires MCP server pattern with `@tool` decorator

### Context Injection Challenge

Even with correct MCP pattern, tools need context:

```python
async def emit_work_output(args):
    basket_id = ???  # How do we get this?
    work_ticket_id = ???  # Claude doesn't know these!

    url = f"{API}/baskets/{basket_id}/work-outputs"
```

MCP tools are stateless functions. They receive `args` from Claude's tool call, but Claude doesn't know about `basket_id`, `work_ticket_id`, etc.

---

## The Solution

### Factory Pattern with Closure

Create a **factory function** that accepts context and returns an MCP server with tools that close over that context.

```python
def create_shared_tools_server(
    basket_id: str,
    work_ticket_id: str,
    agent_type: str
):
    """Factory creates MCP server with context baked in via closure."""

    # Tool definition inside factory scope
    @tool("emit_work_output", "Description", {...})
    async def emit_work_output_with_context(args):
        # Context from closure! ✓
        output_type = args.get('output_type')
        title = args.get('title')

        # Use context from outer scope
        url = f"{API}/baskets/{basket_id}/work-outputs"
        payload = {
            "basket_id": basket_id,
            "work_ticket_id": work_ticket_id,
            "agent_type": agent_type,
            "title": title,
            ...
        }

        # Execute HTTP request
        response = await httpx.post(url, json=payload)
        return {"content": [{"type": "text", "text": json.dumps(response.json())}]}

    # Return MCP server with context-aware tool
    return create_sdk_mcp_server(
        name="shared-agent-tools",
        tools=[emit_work_output_with_context]
    )
```

### Usage in Agent

```python
class ResearchAgentSDK:
    def __init__(self, basket_id, work_ticket_id, ...):
        # Create MCP server with context baked in
        shared_tools = create_shared_tools_server(
            basket_id=basket_id,
            work_ticket_id=work_ticket_id,
            agent_type="research"
        )

        # Register MCP server
        self._options = ClaudeAgentOptions(
            model="claude-sonnet-4-5",
            mcp_servers={"shared_tools": shared_tools},
            allowed_tools=["mcp__shared_tools__emit_work_output"]
        )
```

**Key Insight**: Each agent instance gets its OWN MCP server instance with its OWN context. Context is isolated per agent.

---

## Implementation Pattern

### Step 1: Create Factory in `shared_tools_mcp.py`

```python
"""
Shared Agent Tools - MCP Server Implementation

Factory pattern for creating MCP servers with context closure.
"""

import logging
from typing import Dict, Any
from claude_agent_sdk import tool, create_sdk_mcp_server
import httpx

logger = logging.getLogger(__name__)

# Configuration
SUBSTRATE_API_URL = "https://yarnnn-substrate-api.onrender.com"
SUBSTRATE_SERVICE_SECRET = os.getenv("SUBSTRATE_SERVICE_SECRET")


def create_shared_tools_server(
    basket_id: str,
    work_ticket_id: str,
    agent_type: str,
    user_jwt: Optional[str] = None
):
    """
    Create MCP server with tools that close over provided context.

    This factory function creates a NEW MCP server instance for each agent,
    with tools that have access to agent context via closure.

    Args:
        basket_id: Basket ID for substrate operations
        work_ticket_id: Work ticket ID for output tracking
        agent_type: Agent type (research, content, reporting)
        user_jwt: Optional user JWT for substrate-API auth

    Returns:
        MCP server instance for use in ClaudeAgentOptions.mcp_servers
    """

    # Define tool with context closure
    @tool(
        "emit_work_output",
        """Emit a structured work output for user review.

        Use this tool to record your findings, recommendations, insights, or draft content.
        Each output you emit will be reviewed by the user before any action is taken.

        IMPORTANT: You MUST use this tool for EVERY significant finding or output you generate.
        """,
        {
            "output_type": str,  # finding, recommendation, insight, draft_content, etc.
            "title": str,         # Concise title (max 200 chars)
            "body": dict,         # Structured content with 'summary' field (required)
            "confidence": float,  # 0.0 to 1.0
            "source_block_ids": list  # Optional: provenance tracking
        }
    )
    async def emit_work_output_with_context(args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Emit work output with context from closure.

        Context (basket_id, work_ticket_id, agent_type) is baked into this
        function via closure from the factory function.
        """
        output_type = args.get('output_type')
        title = args.get('title')
        body = args.get('body')
        confidence = args.get('confidence')
        source_block_ids = args.get('source_block_ids', [])

        logger.info(
            f"emit_work_output: type={output_type}, basket={basket_id}, "
            f"ticket={work_ticket_id}, agent={agent_type}"
        )

        try:
            # Call substrate-API to create work_output
            url = f"{SUBSTRATE_API_URL}/api/baskets/{basket_id}/work-outputs"

            payload = {
                "basket_id": basket_id,
                "work_ticket_id": work_ticket_id,
                "output_type": output_type,
                "agent_type": agent_type,
                "title": title,
                "body": body,
                "confidence": confidence,
                "source_context_ids": source_block_ids,
                "metadata": {}
            }

            headers = {
                "X-Service-Name": "work-platform-api",
                "X-Service-Secret": SUBSTRATE_SERVICE_SECRET,
            }
            if user_jwt:
                headers["Authorization"] = f"Bearer {user_jwt}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                work_output = response.json()

            logger.info(
                f"emit_work_output SUCCESS: output_id={work_output.get('id')}, "
                f"type={output_type}, title={title[:50]}"
            )

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "status": "success",
                        "work_output_id": work_output.get('id'),
                        "output_type": output_type,
                        "title": title,
                        "message": f"Work output '{title}' created successfully"
                    }, indent=2)
                }]
            }

        except Exception as e:
            logger.error(f"emit_work_output FAILED: {e}", exc_info=True)
            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps({
                        "status": "error",
                        "error": str(e),
                        "message": "Unexpected error creating work output"
                    })
                }],
                "isError": True
            }

    # Return MCP server with context-aware tool
    return create_sdk_mcp_server(
        name="shared-agent-tools",
        version="1.0.0",
        tools=[emit_work_output_with_context]
    )
```

### Step 2: Use Factory in Agent

```python
from agents_sdk.shared_tools_mcp import create_shared_tools_server

class ResearchAgentSDK:
    def __init__(
        self,
        basket_id: str,
        workspace_id: str,
        work_ticket_id: str,
        ...
    ):
        self.basket_id = basket_id
        self.work_ticket_id = work_ticket_id

        # Create MCP server with context baked in
        shared_tools = create_shared_tools_server(
            basket_id=basket_id,
            work_ticket_id=work_ticket_id,
            agent_type="research"
        )

        # Build Claude SDK options with MCP server
        self._options = ClaudeAgentOptions(
            model="claude-sonnet-4-5",
            system_prompt=self._build_system_prompt(),
            mcp_servers={"shared_tools": shared_tools},
            allowed_tools=[
                "mcp__shared_tools__emit_work_output",  # Custom tool
                "web_search"  # Built-in tool
            ],
            max_tokens=8000
        )

    async def deep_dive(self, topic: str, claude_session_id: Optional[str] = None):
        """Execute research with tool execution."""
        async with ClaudeSDKClient(
            api_key=self.api_key,
            options=self._options
        ) as client:
            # Connect and query
            if claude_session_id:
                await client.connect(session_id=claude_session_id)
            else:
                await client.connect()

            await client.query(f"Research: {topic}")

            # Receive responses (tool execution happens automatically!)
            async for message in client.receive_response():
                # Process message blocks
                pass
```

---

## Examples

### Example 1: ResearchAgent (web_search + emit_work_output)

```python
# Create agent
agent = ResearchAgentSDK(
    basket_id="basket_abc",
    workspace_id="ws_123",
    work_ticket_id="ticket_456"
)

# Execute research
result = await agent.deep_dive("AI agent pricing trends")

# Claude will:
# 1. Call web_search tool (built-in)
# 2. Call emit_work_output tool (custom MCP)
#    - Tool has basket_id="basket_abc" from closure
#    - Tool creates work_output in substrate-API
# 3. Return synthesized response
```

### Example 2: ContentAgent (native subagents + emit_work_output)

```python
# Create agent with platform specialists
agent = ContentAgentSDK(
    basket_id="basket_abc",
    workspace_id="ws_123",
    work_ticket_id="ticket_789",
    enabled_platforms=["twitter", "linkedin"]
)

# Execute content creation
result = await agent.create(
    platform="twitter",
    topic="AI trends",
    content_type="thread"
)

# Claude will:
# 1. Delegate to twitter_specialist subagent (native)
# 2. Call emit_work_output tool (custom MCP)
#    - Tool has agent_type="content" from closure
# 3. Return content draft
```

### Example 3: ReportingAgent (Skills + emit_work_output)

```python
# Create agent with Skills enabled
agent = ReportingAgentSDK(
    basket_id="basket_abc",
    workspace_id="ws_123",
    work_ticket_id="ticket_999",
    default_format="pdf"
)

# Execute report generation
result = await agent.generate(
    report_type="competitive_analysis",
    data_sources=["research_outputs"]
)

# Claude will:
# 1. Call Skill tool for PDF generation (built-in)
# 2. Call code_execution for charts (built-in)
# 3. Call emit_work_output tool (custom MCP)
#    - Tool has work_ticket_id="ticket_999" from closure
# 4. Return PDF report
```

---

## Architecture

### Data Flow

```
User Request
  ↓
Work Orchestration
  ↓
Create Agent Instance
  ├─ basket_id: "basket_abc"
  ├─ work_ticket_id: "ticket_123"
  └─ agent_type: "research"
  ↓
create_shared_tools_server(basket_abc, ticket_123, research)
  ↓ returns MCP server with context in closure
ClaudeAgentOptions(mcp_servers={...})
  ↓
ClaudeSDKClient.connect()
  ↓
Claude calls emit_work_output tool
  ↓ tool has context from closure!
emit_work_output_with_context(args)
  ├─ basket_id from closure: "basket_abc"
  ├─ work_ticket_id from closure: "ticket_123"
  └─ agent_type from closure: "research"
  ↓
POST /api/baskets/basket_abc/work-outputs
  ↓
substrate-API creates work_output
  ↓
Tool returns success to Claude
  ↓
Claude synthesizes response
  ↓
Agent returns result to user
```

### Context Isolation

Each agent instance gets its OWN MCP server with its OWN context:

```python
# Agent 1
agent1 = ResearchAgentSDK(basket_id="basket_1", work_ticket_id="ticket_1")
# Creates: MCP server with context (basket_1, ticket_1, research)

# Agent 2
agent2 = ContentAgentSDK(basket_id="basket_2", work_ticket_id="ticket_2")
# Creates: MCP server with context (basket_2, ticket_2, content)

# Completely isolated! No shared state between agents.
```

---

## Testing

### Unit Test: Factory Pattern

```python
import pytest
from agents_sdk.shared_tools_mcp import create_shared_tools_server

@pytest.mark.asyncio
async def test_factory_creates_isolated_servers():
    """Test that factory creates isolated MCP servers with different contexts."""

    # Create two servers with different contexts
    server1 = create_shared_tools_server(
        basket_id="basket_1",
        work_ticket_id="ticket_1",
        agent_type="research"
    )

    server2 = create_shared_tools_server(
        basket_id="basket_2",
        work_ticket_id="ticket_2",
        agent_type="content"
    )

    # Servers should be different objects
    assert server1 is not server2

    # Each server should have its own tool with its own context
    # (Context is tested via integration test)
```

### Integration Test: Tool Execution

```python
@pytest.mark.asyncio
async def test_emit_work_output_uses_context():
    """Test that emit_work_output tool uses context from closure."""

    # Create agent
    agent = ResearchAgentSDK(
        basket_id="test_basket_123",
        workspace_id="test_workspace",
        work_ticket_id="test_ticket_456"
    )

    # Execute research that triggers emit_work_output
    result = await agent.deep_dive("Test research topic")

    # Verify work_output was created with correct context
    # (Query substrate-API for work_outputs with work_ticket_id=test_ticket_456)
    work_outputs = query_work_outputs(work_ticket_id="test_ticket_456")

    assert len(work_outputs) > 0
    assert work_outputs[0]['basket_id'] == "test_basket_123"
    assert work_outputs[0]['work_ticket_id'] == "test_ticket_456"
    assert work_outputs[0]['agent_type'] == "research"
```

---

## Related Documentation

- **Official SDK Docs**: https://platform.claude.com/docs/en/agent-sdk/custom-tools
- **Claude Agent SDK GitHub**: https://github.com/anthropics/claude-agent-sdk-python
- **MCP Protocol**: https://modelcontextprotocol.io
- **Agent Substrate Architecture**: [AGENT_SUBSTRATE_ARCHITECTURE.md](AGENT_SUBSTRATE_ARCHITECTURE.md)
- **Multi-Agent Orchestration**: [MULTI_AGENT_ORCHESTRATION.md](../canon/MULTI_AGENT_ORCHESTRATION.md)

---

**Pattern Status**: ✅ Production (All specialist agents migrated)
**Last Validated**: 2025-11-20
**Migration Commits**: e58ab208, cc6b1bf6
