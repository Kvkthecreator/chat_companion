# Claude Agent SDK Selection Rationale

**Why YARNNN Uses Claude Agent SDK Over Raw API or Alternative Frameworks**

**Version**: 1.0
**Date**: 2025-11-18
**Status**: ✅ Canonical - Architecture Decision Record
**Category**: Infrastructure Decision
**Audience**: Engineering, Architecture, Future Team Members

---

## 🎯 Purpose of This Document

This document permanently captures **why YARNNN selected the Claude Agent SDK** over alternatives (raw Anthropic API, OpenAI Agents SDK, custom frameworks). It exists to:

1. **Prevent confusion** between Claude API (simple LLM calls) vs Claude Agent SDK (agentic infrastructure)
2. **Document decision rationale** so future team members understand the architectural choice
3. **Preserve research context** - links, concepts, distinctions that took significant time to discern
4. **Avoid re-litigating** this decision without new information

**Critical Distinction:**
- **Claude API** = Make LLM calls, get text responses (like ChatGPT API)
- **Claude Agent SDK** = Full agentic infrastructure with Skills, subagents, session management, MCP tools

---

## ⚠️ The Confusion This Document Resolves

### Initial Misconception (2025-11-17)

The work-platform initially implemented agents using **raw Anthropic API**:

```python
# What we built initially (WRONG PATTERN)
from anthropic import AsyncAnthropic

client = AsyncAnthropic(api_key=key)
response = await client.messages.create(
    model="claude-sonnet-4-5",
    tools=[EMIT_WORK_OUTPUT_TOOL],
    messages=[{"role": "user", "content": task}]
)
# Parse response, extract tool calls, done
```

**Problems with this approach:**
1. No agentic loop (single-shot only)
2. No session management (we'd have to build it)
3. No Skills (organizational context = bloated prompts)
4. No subagents (would require custom orchestration)
5. Conversation history management = our responsibility
6. Reinventing infrastructure that Claude Agent SDK provides

### Why This Happened

- Claude Agent SDK documentation wasn't clearly distinguished from Claude API docs
- The SDK requires Node.js + CLI (seemed like extra complexity)
- Initial prototyping used simpler API pattern
- No clear comparison of SDK features vs raw API

**This document ensures we never make this mistake again.**

---

## 📊 The Decision Matrix

### Options Evaluated (2025-11-17 to 2025-11-18)

| Option | Description | Verdict |
|--------|-------------|---------|
| **Raw Anthropic API** | Direct `messages.create()` calls | ❌ Too low-level, reinvents infrastructure |
| **Claude Agent SDK** | Full agentic framework from Anthropic | ✅ **SELECTED** - Perfect alignment with YARNNN thesis |
| **OpenAI Agents SDK** | Provider-agnostic agent framework | ❌ Missing Skills, requires manual session mgmt |
| **Custom Framework** | Build our own agent loop | ❌ Undifferentiated heavy lifting |

---

## ✅ Why Claude Agent SDK Was Selected

### 1. Skills = Organizational Context (YARNNN's Core Thesis)

**The Problem:**
YARNNN's value proposition is **"context understanding enables superior agent reasoning"**. We need to provide agents with:
- Research methodologies
- Quality standards
- Output templates
- Substrate query patterns
- Work output structures

**Raw API Approach:**
- Stuff everything into system prompts (context bloat, $$$)
- OR retrieve dynamically (reinventing Skills)

**Claude Agent SDK Solution:**
Skills provide **procedural knowledge at zero token cost until relevant**.

```markdown
# .claude/skills/yarnnn-research/SKILL.md
---
name: yarnnn-research-methodology
description: Research methodology for YARNNN substrate-backed intelligence
---

## Workflow
1. Query substrate for existing knowledge (avoid redundancy)
2. Identify knowledge gaps from substrate blocks
3. Conduct targeted research on gaps only
4. Structure findings as work outputs (finding/insight/recommendation)
5. Track provenance to source blocks

## Quality Standards
- Confidence >0.8 requires primary sources
- Always link to source_block_ids
- Findings must extend substrate, not duplicate

## Templates
[Templates for structured outputs]
```

**Progressive Loading:**
- Metadata (100 tokens) always loaded
- Instructions (~5k tokens) loaded when relevant
- Resources (scripts, templates) accessed via bash (no context tokens)

**Why This Matters:**
- Skills embed YARNNN's organizational context (substrate patterns, quality standards)
- No token cost until needed
- Reusable across all agents
- **This IS the moat** - organizational intelligence encoded as Skills

**Documentation:**
- Official Docs: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- Key Insight: "Skills package instructions, metadata, and resources that Claude uses automatically when relevant"

---

### 2. Built-in Session Management (Not Our Value-Add)

**The Problem:**
Agents need conversation history for multi-turn reasoning. Managing this is:
- Low-value work (infrastructure plumbing)
- High-risk (memory bloat, compaction complexity)
- Not YARNNN's differentiator

**Raw API Approach:**
```python
# We'd have to manage this ourselves
messages = []
messages.append({"role": "user", "content": "Research competitors"})
response = await client.messages.create(messages=messages)
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": "Now analyze pricing"})
# Manage history growth, compaction, persistence, cleanup...
```

**Claude Agent SDK Solution:**
- Built-in session management via Claude Code infrastructure
- Sessions stored/resumed automatically
- **Auto-compaction** for long conversations
- We don't touch conversation history

**Why This Matters:**
- Focus engineering time on YARNNN's moat (substrate ↔ work integration)
- Avoid conversation memory bloat (known risk, managed by SDK)
- Session resumption out-of-the-box

**Documentation:**
- Session Management: https://docs.claude.com/en/docs/agent-sdk/hosting
- Key Quote: "Sessions don't timeout automatically" - built-in persistence

---

### 3. Subagents = YARNNN's Multi-Agent Architecture

**The Vision:**
YARNNN's architecture includes specialized agent types:
- **Research Agent** with subagents:
  - Market Intelligence (track trends)
  - Competitor Tracker (deep analysis)
  - Social Listener (social signals)
  - Analyst (synthesis)

**Raw API Approach:**
- Build custom orchestration
- Manage context isolation manually
- Sequential execution unless we build parallelization

**Claude Agent SDK Solution:**
```javascript
agents: {
  'market-intelligence': {
    description: 'Track market trends and competitor movements',
    prompt: 'You monitor markets and identify signals...',
    tools: ['query_substrate', 'web_search', 'emit_work_output'],
    model: 'sonnet'  // Cost-efficient for monitoring
  },
  'competitor-tracker': {
    description: 'Deep analysis of specific competitors',
    prompt: 'You analyze competitor strategy...',
    tools: ['query_substrate', 'web_search', 'emit_work_output'],
    model: 'opus'  // More powerful for deep analysis
  },
  'analyst': {
    description: 'Synthesize findings into insights',
    prompt: 'You synthesize research into actionable insights...',
    tools: ['query_substrate', 'emit_work_output'],
    model: 'sonnet'
  }
}
```

**Key Features:**
- **Context Isolation:** Each subagent has clean context (no bloat)
- **Parallel Execution:** Built-in concurrency
- **Model Selection:** Different models per subagent (cost optimization)
- **Tool Restriction:** Limit tools per subagent (security)

**Why This Matters:**
- Direct mapping to YARNNN's planned agent hierarchy
- Context isolation prevents the "everything in one prompt" problem
- Parallel execution = faster research workflows
- Declarative definition (no orchestration code)

**Documentation:**
- Subagents Overview: https://docs.claude.com/en/docs/agent-sdk/subagents
- Key Quote: "Context isolation prevents information overload"

---

### 4. MCP Tools = YARNNN's Integration Layer

**The Integration Challenge:**
YARNNN agents need to:
- Query substrate for context blocks
- Emit work outputs for supervision
- Get reference assets
- (Future) Search web, analyze data

**Raw API Approach:**
- Define tools as JSON schemas
- Parse tool_use responses
- Execute tools in our code
- Return tool_result messages
- Build the agentic loop ourselves

**Claude Agent SDK Solution:**
MCP (Model Context Protocol) provides standard tool integration:

```python
from claude_agent_sdk import create_sdk_mcp_server, tool

@tool("query_substrate", "Query YARNNN substrate for context blocks", {
    "query": str,
    "limit": int,
    "min_similarity": float
})
async def query_substrate(args):
    """Semantic search across substrate blocks."""
    return await substrate_client.semantic_search(
        query=args["query"],
        limit=args.get("limit", 10),
        min_similarity=args.get("min_similarity", 0.7)
    )

@tool("emit_work_output", "Submit structured work output", {
    "output_type": str,
    "title": str,
    "body": dict,
    "confidence": float,
    "source_block_ids": list
})
async def emit_work_output(args):
    """Write work output to substrate-API via BFF."""
    return await work_output_service.create(
        output_type=args["output_type"],
        title=args["title"],
        body=args["body"],
        confidence=args["confidence"],
        source_context_ids=args["source_block_ids"]
    )

yarnnn_mcp = create_sdk_mcp_server(
    name="yarnnn",
    version="1.0.0",
    tools=[query_substrate, emit_work_output, get_reference_assets]
)
```

**Why This Matters:**
- Standard protocol (MCP is Anthropic's ecosystem standard)
- Clean separation (tools live in work-platform, called by agents)
- Growing ecosystem (future tools via MCP marketplace)
- In-process execution (no subprocess overhead like external MCP servers)

**Documentation:**
- MCP Overview: https://github.com/anthropics/courses/blob/master/tool_use/01_tool_use_overview.ipynb
- SDK MCP: Built-in support via `create_sdk_mcp_server()`

---

### 5. Hosting Flexibility = Deployment Options

**Deployment Patterns Supported:**

1. **Ephemeral Sessions** (current plan)
   - Create container per work session
   - Destroy when complete
   - Good for: One-off research tasks

2. **Long-Running Sessions** (future)
   - Persistent containers
   - Good for: Proactive monitoring, continuous agents

3. **Hybrid Sessions** (future)
   - Ephemeral containers hydrated with historical state
   - Good for: Multi-day projects

**Infrastructure Requirements:**
- Python 3.10+ ✅ (already have)
- Node.js 18+ ⚠️ (REQUIRED - Claude Code CLI dependency)
- Claude Code CLI ⚠️ (REQUIRED - Python SDK is a wrapper)
- ~1GB RAM, 5GB disk ✅ (Render supports)

**Critical Understanding:**
The Python SDK is **NOT standalone** - it wraps the Claude Code CLI (which requires Node.js). The SDK communicates with the CLI via subprocess. Architecture:

```
Python SDK (your code)
    ↓ subprocess calls
Claude Code CLI (Node.js process)
    ↓ API calls
Claude API (Anthropic)
```

**Why This Matters:**
- You MUST install Node.js even though you're using Python
- You MUST install Claude Code CLI globally (`npm install -g`)
- The SDK cannot function without CLI in system PATH
- Runtime has both Python and Node.js processes

**Render Compatibility:**
```dockerfile
# Dockerfile for work-platform (Render)
FROM python:3.10

# Install Node.js (REQUIRED for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

# Install Claude Code CLI (REQUIRED for Python SDK)
RUN npm install -g @anthropic-ai/claude-code

# Verify Claude Code installation
RUN claude-code --version

# Install Python deps (includes claude-agent-sdk)
COPY requirements.txt .
RUN pip install -r requirements.txt

# App code
COPY . /app
WORKDIR /app

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Cost Profile:**
- Container: ~$0.05/hour (minimal)
- Tokens: Dominant cost (same as raw API)
- No premium for using SDK
- Extra process overhead: Python + Node.js (CLI) running simultaneously

**Documentation:**
- Hosting Guide: https://docs.claude.com/en/docs/agent-sdk/hosting
- Python SDK Docs: https://docs.claude.com/en/docs/agent-sdk/python
- Key Quote: "A minimum cost is roughly 5 cents per hour running"

---

### ⚠️ Critical Architecture Understanding: Python SDK = CLI Wrapper

**This is important to understand before proceeding:**

The Claude Agent SDK for Python is **NOT** a direct API client. It's a **wrapper around the Claude Code CLI**.

**What this means:**
```
┌─────────────────────────────────────┐
│  Your Python Code                   │
│  (uses claude-agent-sdk)            │
└────────────┬────────────────────────┘
             │ subprocess.Popen()
             │ stdin/stdout communication
             ▼
┌─────────────────────────────────────┐
│  Claude Code CLI                    │
│  (Node.js process)                  │
│  (@anthropic-ai/claude-code)        │
└────────────┬────────────────────────┘
             │ HTTP requests
             ▼
┌─────────────────────────────────────┐
│  Claude API                         │
│  (Anthropic infrastructure)         │
└─────────────────────────────────────┘
```

**Implications:**
1. **Node.js is NOT optional** - Even though you're writing Python, you MUST have Node.js installed
2. **Two runtimes running** - Python (your app) + Node.js (CLI subprocess)
3. **Subprocess overhead** - IPC communication between Python and Node.js processes
4. **Deployment complexity** - Must install both Python and Node.js dependencies
5. **Error surface** - Errors can occur in Python SDK, CLI subprocess, or API layer

**Why Anthropic Built It This Way:**
- Claude Code CLI is their battle-tested agentic infrastructure (powers Claude Code product)
- Python SDK provides Python-friendly API to that infrastructure
- Avoids reimplementing agentic loop in Python
- Ensures feature parity across SDK languages (TypeScript, Python both use same CLI)

**Trade-off Acceptance:**
Yes, this adds deployment complexity (Node.js + CLI). But:
- ✅ We get battle-tested agentic infrastructure
- ✅ Skills, subagents, session management work out-of-box
- ✅ No need to build agentic loop ourselves
- ✅ Organizational context (Skills) is worth the complexity

**Alternative Considered:**
Raw Anthropic API (Python-only, no Node.js) was rejected because:
- ❌ No Skills (organizational context in prompts = bloat)
- ❌ No session management (we'd build it)
- ❌ No subagents (custom orchestration)
- ❌ Agentic loop = our responsibility

**The Node.js dependency is justified by the value Skills + subagents + session management provide.**

---

## 🚫 Why Alternatives Were Rejected

### Raw Anthropic API

**Reasons for Rejection:**
1. No Skills (would bloat prompts with organizational context)
2. No session management (we'd build it ourselves)
3. No subagents (custom orchestration required)
4. Agentic loop = our responsibility
5. Conversation history = our responsibility
6. **Reinventing infrastructure that SDK provides**

**When to Use Raw API:**
- Simple, single-shot LLM calls
- No multi-turn reasoning needed
- No organizational context
- Stateless interactions

**Not Appropriate for YARNNN Because:**
- We need multi-turn reasoning (work sessions)
- We need organizational context (research methodology, quality standards)
- We need session persistence (long-running work)
- We need subagent orchestration (specialized research)

---

### OpenAI Agents Python SDK

**What It Provides:**
- Generic agent framework
- Provider-agnostic (100+ LLMs via LiteLLM)
- Handoffs for multi-agent orchestration
- Built-in session backends (SQLite, Redis, PostgreSQL)
- Structured outputs

**Reasons for Rejection:**

#### 1. No Skills Equivalent
OpenAI SDK only has:
- Tools (function_tool decorator)
- System prompts (static instructions)
- Handoffs (agent delegation)

To provide organizational context, you must:
- Stuff into system prompts (context bloat, $$)
- OR build custom retrieval (reinventing Skills)

**Skills are critical for YARNNN** - they embed substrate patterns, research methodology, quality standards at zero token cost.

#### 2. Session Management = Our Responsibility
```python
# OpenAI SDK - you manage sessions
from agents import SQLiteSession, Runner

session = SQLiteSession("sessions.db")
result = await Runner.run(agent, input, session=session)
# You manage: history growth, compaction, cleanup
```

vs.

```python
# Claude Agent SDK - sessions managed for you
result = await query(prompt, options={...})
# Session automatically managed, compacted, persisted
```

**We don't want to manage conversation history** - it's undifferentiated heavy lifting.

#### 3. Handoffs ≠ Subagents
```python
# OpenAI SDK - handoffs are sequential
planner = Agent(name="Planner", ...)
researcher = Agent(name="Researcher", ...)
synthesizer = Agent(name="Synthesizer", ...)

coordinator = Agent(
    name="Coordinator",
    handoffs=[planner, researcher, synthesizer]
)
# Coordinator hands off to planner → researcher → synthesizer
# Sequential execution, shared history
```

vs.

```python
# Claude Agent SDK - subagents are parallel + isolated
agents: {
  'planner': {...},
  'researcher': {...},
  'synthesizer': {...}
}
# Parallel execution, context isolation
```

**YARNNN needs parallel subagents with context isolation** - not sequential handoffs.

#### 4. Provider-Agnostic = Not an Advantage
Yes, OpenAI SDK supports 100+ models via LiteLLM. But:
- We're committed to Claude (quality, extended thinking, reliability)
- Provider-agnostic means lowest-common-denominator features
- Claude-specific features (Skills, compaction) not available

**We'd rather optimize for Claude than support all models.**

**Documentation:**
- OpenAI Agents SDK: https://github.com/openai/openai-agents-python
- Our Analysis: Conducted 2025-11-18, concluded Skills gap is disqualifying

---

### Custom Framework

**Why We Don't Build Our Own:**
1. **Undifferentiated heavy lifting** - agentic loops are solved problems
2. **Maintenance burden** - every Claude API change requires updates
3. **Feature gap** - Skills, compaction, session management take months to build
4. **Not our moat** - YARNNN's value is substrate ↔ work integration, not agent framework

**When to Build Custom:**
- No existing solution meets needs
- Unique requirements justify investment
- Framework itself is the product

**Not Appropriate for YARNNN Because:**
- Claude Agent SDK exists and fits perfectly
- Our moat is elsewhere (substrate, governance, work supervision)
- Engineering time better spent on differentiation

---

## 📖 Key Concepts Reference (Permanent)

### Skills vs Tools: The Critical Distinction

**Tools = Actions Claude Can Take**
```python
@tool("send_email", "Send an email", {"to": str, "subject": str, "body": str})
async def send_email(args):
    # Execute action
    return await email_service.send(...)
```

- What: Specific executable functions
- When invoked: Claude decides based on task
- Token cost: Tool definition + execution result
- Example: `send_email`, `query_database`, `fetch_weather`

**Skills = Procedural Knowledge + Context**
```markdown
# .claude/skills/email-triage/SKILL.md
---
name: email-triage-workflow
description: Email triage and response methodology
---

## Workflow
1. Classify email by urgency (high/medium/low)
2. Check sender history for context
3. Draft response using templates
4. Flag for review if sensitive

## Templates
- Standard response: [template]
- Escalation: [template]
```

- What: Instructions, workflows, templates, organizational context
- When loaded: Metadata always (100 tokens), full content when relevant
- Token cost: Near-zero until needed (progressive disclosure)
- Example: Research methodology, code review checklist, customer support workflows

**Key Insight:**
> "Tools are the primary building blocks of execution. Skills provide procedural knowledge that Claude uses automatically when relevant."

**For YARNNN:**
- **Tools:** `query_substrate`, `emit_work_output`, `get_reference_assets`
- **Skills:** Research methodology, quality standards, output templates, substrate patterns

**Why Skills Matter:**
Organizational context (research workflows, quality standards) would cost thousands of tokens if embedded in prompts. Skills provide this at ~100 tokens (metadata only) until relevant.

---

### Subagents vs Handoffs

**Subagents (Claude Agent SDK):**
```javascript
agents: {
  'specialist-a': {
    description: 'Handles task type A',
    prompt: 'You are an expert at A...',
    tools: ['tool1', 'tool2'],
    model: 'sonnet'
  },
  'specialist-b': {
    description: 'Handles task type B',
    prompt: 'You are an expert at B...',
    tools: ['tool3', 'tool4'],
    model: 'opus'
  }
}
```

- **Execution:** Parallel (both run concurrently)
- **Context:** Isolated (each has clean context)
- **Invocation:** Automatic (based on description + task)
- **Tools:** Restricted per subagent
- **Model:** Different per subagent

**Handoffs (OpenAI Agents SDK):**
```python
agent_a = Agent(name="A", handoffs=[agent_b])
agent_b = Agent(name="B", handoffs=[agent_c])
```

- **Execution:** Sequential (A → B → C)
- **Context:** Shared (conversation history flows)
- **Invocation:** Explicit (agent decides to hand off)
- **Tools:** Per agent definition
- **Model:** Per agent definition

**For YARNNN:**
Research workflow needs **parallel execution** with **context isolation**:
- Market Intelligence + Competitor Tracker + Social Listener run in parallel
- Each subagent has focused context (not bloated with others' findings)
- Analyst subagent synthesizes results

**Subagents are the right pattern.**

---

### Session Types: Ephemeral vs Long-Running

**Ephemeral Sessions:**
```python
# Create container for task, destroy when done
async def handle_work_session(task_id):
    result = await query(
        prompt=f"Research: {task_intent}",
        options={...}
    )
    # Session ends, container destroyed
    return result
```

- **Use Case:** One-off tasks (research, content generation)
- **Cost:** Per-execution
- **State:** Stateless (hydrated from DB if needed)
- **YARNNN Fit:** ✅ Perfect for work sessions

**Long-Running Sessions:**
```python
# Maintain persistent container
async def run_continuous_agent():
    while True:
        tasks = await poll_for_tasks()
        for task in tasks:
            result = await query(task, options={...})
        await asyncio.sleep(60)
```

- **Use Case:** Monitoring, proactive agents
- **Cost:** Continuous container cost (~$0.05/hr)
- **State:** Persistent
- **YARNNN Fit:** 🔮 Future (proactive monitoring agents)

**Hybrid Sessions:**
```python
# Ephemeral container + historical state
async def handle_multi_day_project(project_id):
    # Hydrate from DB
    history = await load_project_history(project_id)

    result = await query(
        prompt="Continue work on project",
        options={"resume_session": history}
    )
    # Session ends, state saved to DB
```

- **Use Case:** Multi-day projects, intermittent work
- **Cost:** Per-execution + state storage
- **State:** Hydrated/dehydrated
- **YARNNN Fit:** 🔮 Future (long-running research projects)

**Current Plan:** Ephemeral sessions for work sessions (one task = one container)

---

### MCP Tools: In-Process vs External

**In-Process MCP (What We'll Use):**
```python
from claude_agent_sdk import create_sdk_mcp_server, tool

@tool("query_substrate", "...", {...})
async def query_substrate(args):
    return await substrate_client.search(...)

yarnnn_mcp = create_sdk_mcp_server(
    name="yarnnn",
    tools=[query_substrate, ...]
)

# Use in agent
options = ClaudeAgentOptions(
    mcp_servers={"yarnnn": yarnnn_mcp}
)
```

- **Execution:** Same Python process
- **Performance:** No IPC overhead
- **Deployment:** Bundled with app
- **Use Case:** Custom business logic (YARNNN substrate, work outputs)

**External MCP (Future):**
```python
# Reference external MCP server
options = ClaudeAgentOptions(
    mcp_servers={
        "web-search": "mcp://tavily-search-server"
    }
)
```

- **Execution:** Separate process/service
- **Performance:** IPC overhead
- **Deployment:** External dependency
- **Use Case:** Third-party integrations (Tavily search, Firecrawl, etc.)

**YARNNN Strategy:**
- In-process MCP for substrate/work integration (core logic)
- External MCP for third-party services (search, data sources)

---

## 🔗 Essential Documentation Links

### Official Claude Agent SDK Documentation

**Core SDK:**
- Overview: https://docs.claude.com/en/docs/agent-sdk/overview
- Installation: https://docs.claude.com/en/docs/agent-sdk/installation
- Hosting: https://docs.claude.com/en/docs/agent-sdk/hosting

**Skills:**
- Overview: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview
- Creating Skills: https://docs.claude.com/en/docs/agents-and-tools/agent-skills/creating-skills
- Progressive Loading: Described in overview (metadata → instructions → resources)

**Subagents:**
- Overview: https://docs.claude.com/en/docs/agent-sdk/subagents
- Configuration: Programmatic via `agents` parameter (recommended for SDK)

**MCP Tools:**
- Tool Use Notebook: https://github.com/anthropics/courses/blob/master/tool_use/01_tool_use_overview.ipynb
- SDK MCP: `create_sdk_mcp_server()` for in-process tools

**Key Blog Post:**
- Building Agents: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- Covers: Skills philosophy, context efficiency, organizational knowledge

### Comparison Resources

**OpenAI Agents SDK:**
- Repository: https://github.com/openai/openai-agents-python
- Documentation: https://openai.github.io/openai-agents-python/
- Our Analysis: 2025-11-18, concluded Skills gap disqualifies it for YARNNN

**Raw Anthropic API:**
- Messages API: https://docs.anthropic.com/en/api/messages
- Tool Use: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
- Use Case: Single-shot LLM calls, not agentic workflows

---

## 📋 Decision Summary

### Selected: Claude Agent SDK

**Core Rationale:**
1. **Skills** embed organizational context (YARNNN's moat) at zero token cost
2. **Built-in session management** lets us focus on substrate ↔ work integration
3. **Subagents** with context isolation match our multi-agent architecture
4. **MCP tools** provide clean integration layer
5. **Hosting flexibility** supports current (ephemeral) and future (long-running) patterns

**Trade-offs Accepted:**
- Node.js + CLI dependency (manageable on Render)
- Claude-only (not provider-agnostic) - acceptable, Claude is our choice
- SDK learning curve (documented in this file)

**Alignment with YARNNN Thesis:**
> **"Context understanding + Work supervision = Superior AI outcomes"**

Claude Agent SDK's **Skills architecture directly enables the context understanding** that powers YARNNN's flywheel.

---

## 🚀 Next Steps

1. **Read Implementation Plan:** See `CLAUDE_AGENT_SDK_IMPLEMENTATION_PLAN.md` (working document)
2. **Setup Infrastructure:** Node.js + Claude Code CLI on Render
3. **Build MCP Tools:** `query_substrate`, `emit_work_output`, `get_reference_assets`
4. **Define Skills:** Research methodology, quality standards, output templates
5. **Scaffold Research Agent:** With subagents (market intel, competitor, analyst)

---

## 📎 See Also

### YARNNN Canon
- [YARNNN_PLATFORM_CANON_V4.md](./YARNNN_PLATFORM_CANON_V4.md) - Core philosophy
- [YARNNN_WORK_PLATFORM_THESIS.md](./YARNNN_WORK_PLATFORM_THESIS.md) - Context + Work thesis
- [AGENT_SUBSTRATE_ARCHITECTURE.md](./AGENT_SUBSTRATE_ARCHITECTURE.md) - Integration architecture
- [TERMINOLOGY_GLOSSARY.md](./TERMINOLOGY_GLOSSARY.md) - Terminology reference

### Implementation
- [CLAUDE_AGENT_SDK_IMPLEMENTATION_PLAN.md](../architecture/CLAUDE_AGENT_SDK_IMPLEMENTATION_PLAN.md) - Scaffolding plan (working doc)

---

**This decision is canonical. Refer to this document before questioning the Claude Agent SDK choice.**

**Last Updated:** 2025-11-18
**Decision Made By:** Architecture review with comprehensive SDK evaluation
**Reviewers:** Engineering team
# Claude Agent SDK Skills: Implementation Guide
**Date**: November 19, 2025
**Source**: [claude-cookbooks/skills](https://github.com/anthropics/claude-cookbooks/tree/b29ec6f109c0379fa2eb620611a3d504e28fba09/skills)
**Purpose**: Technical reference for implementing Skills in YARNNN agents

---

## 1. Skills Setup (Python SDK)

### Required Beta Headers

```python
from anthropic import Anthropic

client = Anthropic(
    api_key="your-anthropic-api-key",
    default_headers={
        "anthropic-beta": "code-execution-2025-08-25,files-api-2025-04-14,skills-2025-10-02"
    }
)
```

**Three beta headers are mandatory**:
1. `code-execution-2025-08-25` — Activates skill execution capabilities
2. `files-api-2025-04-14` — Enables file retrieval functionality
3. `skills-2025-10-02` — Unlocks the Skills feature itself

---

## 2. Skill Invocation Pattern

### Basic Invocation

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",  # Latest model
    max_tokens=4096,

    # SKILLS SPECIFICATION
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },

    # REQUIRED: Code execution tool must be present
    tools=[
        {"type": "code_execution_20250825", "name": "code_execution"}
    ],

    messages=[
        {"role": "user", "content": "Create an Excel file with Q4 sales data"}
    ]
)
```

### Built-in Skill IDs

| skill_id | Capability | Output Format | Example Use Case |
|----------|-----------|---------------|------------------|
| `xlsx` | Excel workbook creation | `.xlsx` | Data tables, formulas, charts |
| `pptx` | PowerPoint presentations | `.pptx` | Slide decks, presentations |
| `pdf` | PDF document generation | `.pdf` | Reports, formatted documents |
| `docx` | Word documents | `.docx` | Written content, formatting |

### Multiple Skills in Single Request

```python
container={
    "skills": [
        {"type": "anthropic", "skill_id": "xlsx", "version": "latest"},
        {"type": "anthropic", "skill_id": "pdf", "version": "latest"},
    ]
}
```

**Benefit**: Claude can decide which skill to use based on user intent.

---

## 3. File Output Handling

### Response Structure

Skills return `file_id` attributes embedded in response blocks:

```python
response = client.messages.create(...)

# Response structure:
# response.content = [
#     ContentBlock(type="text", text="I've created the Excel file..."),
#     ContentBlock(
#         type="tool_use",
#         id="toolu_...",
#         name="code_execution",
#         input={...}
#     ),
#     ContentBlock(
#         type="tool_result",
#         tool_use_id="toolu_...",
#         content=[...],  # Contains file_id reference
#     )
# ]
```

### Extracting file_id from Response

```python
def extract_file_ids(response):
    """Extract all file_ids from Claude response"""
    file_ids = []

    for block in response.content:
        if block.type == "tool_result":
            # file_id may be in different formats depending on response structure
            content = str(block.content) if hasattr(block, 'content') else str(block)

            # Pattern: file_01AbCdEfGhIjKl...
            import re
            matches = re.findall(r'file_[A-Za-z0-9]{22}', content)
            file_ids.extend(matches)

    return list(set(file_ids))  # Deduplicate
```

### Downloading Files via Files API

```python
# Method 1: Download file content
file_content = client.beta.files.download(file_id="file_01AbCdEf...")

# IMPORTANT: Use .read() method, not .content attribute
with open("output.xlsx", "wb") as f:
    f.write(file_content.read())  # ✅ Correct

# ❌ WRONG: file_content.content will fail
```

### Retrieving File Metadata

```python
# Get metadata without downloading full file
metadata = client.beta.files.retrieve_metadata(file_id="file_01AbCdEf...")

# Available attributes:
# - metadata.id: file_01AbCdEf...
# - metadata.filename: "sales_report.xlsx"
# - metadata.size_bytes: 45231  # ✅ Use size_bytes, not size
# - metadata.created_at: "2025-11-19T..."
```

### Files API Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `client.beta.files.download(file_id)` | Download binary content | File stream (use `.read()`) |
| `client.beta.files.retrieve_metadata(file_id)` | Get metadata | Filename, size_bytes, created_at |
| `client.beta.files.list()` | List all files | Array of file metadata |
| `client.beta.files.delete(file_id)` | Remove file | Deletion confirmation |

---

## 4. Complete Example: Generate & Download Excel File

```python
from anthropic import Anthropic
import re

# Initialize client with Skills support
client = Anthropic(
    api_key="sk-ant-...",
    default_headers={
        "anthropic-beta": "code-execution-2025-08-25,files-api-2025-04-14,skills-2025-10-02"
    }
)

# Request Excel generation
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    container={
        "skills": [
            {"type": "anthropic", "skill_id": "xlsx", "version": "latest"}
        ]
    },
    tools=[
        {"type": "code_execution_20250825", "name": "code_execution"}
    ],
    messages=[
        {
            "role": "user",
            "content": """Create an Excel spreadsheet with:
            - Sheet 1: Sales data (columns: Month, Revenue, Expenses)
            - Sheet 2: Chart showing revenue trends
            - Include formulas for totals"""
        }
    ]
)

# Extract file_id
file_ids = []
for block in response.content:
    if block.type == "tool_result":
        matches = re.findall(r'file_[A-Za-z0-9]{22}', str(block.content))
        file_ids.extend(matches)

if file_ids:
    file_id = file_ids[0]

    # Get metadata
    metadata = client.beta.files.retrieve_metadata(file_id=file_id)
    print(f"Filename: {metadata.filename}")
    print(f"Size: {metadata.size_bytes} bytes")

    # Download file
    file_content = client.beta.files.download(file_id=file_id)

    # Save locally
    with open(f"outputs/{metadata.filename}", "wb") as f:
        f.write(file_content.read())

    print(f"✅ File saved: outputs/{metadata.filename}")
else:
    print("❌ No file_id found in response")
```

---

## 5. Integration with YARNNN Work Orchestration

### work_outputs Schema Integration

```python
from models.work_output import WorkOutput

# After generating file via Skill
file_id = extract_file_ids(response)[0]
metadata = client.beta.files.retrieve_metadata(file_id=file_id)

# Create work_output record
work_output = WorkOutput(
    work_ticket_id=work_ticket_id,
    basket_id=basket_id,
    agent_type="reporting",
    output_type="spreadsheet",
    title="Q4 Sales Analysis",

    # FILE OUTPUT (not text)
    body=None,
    file_id=file_id,
    file_format="xlsx",
    file_size_bytes=metadata.size_bytes,
    mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    # PROVENANCE
    generation_method="skill",
    skill_metadata={
        "skill_id": "xlsx",
        "skill_name": "Excel Spreadsheet Generator",
        "skill_version": "latest",
        "container_id": response.container.id if hasattr(response, 'container') else None,
        "execution_time_ms": calculate_execution_time(response),
    },

    # OPTIONAL: Download and store in Supabase Storage
    storage_path=None,  # Set after uploading to storage
)

db.create_work_output(work_output)
```

### Optional: Persist to Supabase Storage

```python
# Download file from Claude Files API
file_content = client.beta.files.download(file_id=file_id)

# Upload to Supabase Storage
storage_path = f"baskets/{basket_id}/work_outputs/{work_ticket_id}/{metadata.filename}"

supabase.storage.from_("work-outputs").upload(
    path=storage_path,
    file=file_content.read(),
    file_options={"content-type": work_output.mime_type}
)

# Update work_output with storage_path
work_output.storage_path = storage_path
db.update_work_output(work_output)
```

---

## 6. Best Practices & Gotchas

### Critical Implementation Details

1. **Files are temporary on Anthropic servers**
   - Download and save locally/to Supabase Storage immediately
   - File retention period is undocumented (assume short-lived)

2. **Use correct attribute names**
   - ✅ `.read()` method when downloading
   - ❌ NOT `.content` attribute
   - ✅ `size_bytes` property for file metadata
   - ❌ NOT `size`

3. **Code execution tool is REQUIRED**
   - Skills don't work without `code_execution` tool
   - Skills guide Claude to write code → code tool executes → files generated

4. **Progressive disclosure optimization**
   - Skills load dynamically only when invoked
   - Avoids unnecessary token overhead
   - Multiple skills in same request = Claude chooses best one

5. **Rerunning overwrites files**
   - Watch for `[overwritten]` indicators in responses
   - Each run creates new file_id

### Token Optimization

**Batch operations** for efficiency:
```python
# ✅ Good: Single request, multiple outputs
messages=[{
    "role": "user",
    "content": """Create:
    1. Excel file with data
    2. PDF report summarizing the data
    3. PowerPoint presentation with key findings"""
}]

# ❌ Wasteful: Three separate requests
# (loses conversation context, uses more tokens)
```

### Error Handling

```python
try:
    response = client.messages.create(...)
    file_ids = extract_file_ids(response)

    if not file_ids:
        # Skill may have failed or not generated file
        print("Warning: No file generated")
        # Fall back to text output

    for file_id in file_ids:
        try:
            metadata = client.beta.files.retrieve_metadata(file_id=file_id)
            file_content = client.beta.files.download(file_id=file_id)
            # Process file...
        except Exception as e:
            print(f"Error downloading {file_id}: {e}")
            # Continue with other files

except Exception as e:
    print(f"Skill invocation failed: {e}")
    # Handle gracefully
```

---

## 7. Custom Skills (Future)

**Structure**:
```
.claude/skills/my-custom-skill/
├── SKILL.md              # Instructions (YAML frontmatter + markdown)
├── scripts/              # Python/Bash automation
├── references/           # Documentation
└── assets/               # Templates, binaries
```

**SKILL.md Format**:
```markdown
---
name: "custom_skill_name"
description: "What the skill does"
allowed-tools: "Read,Write,Bash,Glob,Grep,Edit"
license: "MIT"
version: "1.0.0"
model: "claude-sonnet-4.5"  # Optional
---

# Skill Instructions

When the user asks for [specific task], do the following:

1. [Step 1]
2. [Step 2]
...
```

**Note**: Custom skills not yet implemented in YARNNN. Start with Anthropic-provided skills (PDF, XLSX, DOCX, PPTX).

---

## 8. Next Steps for YARNNN Integration

### Phase 1: Enable Skills in ReportingAgentSDK ✅

```python
# yarnnn_agents/reporting_agent.py
class ReportingAgentSDK:
    def __init__(self, ...):
        self.client = Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            default_headers={
                "anthropic-beta": "code-execution-2025-08-25,files-api-2025-04-14,skills-2025-10-02"
            }
        )

    def generate_report(self, topic: str, format: str = "text", ...):
        if format in ["pdf", "xlsx", "docx", "pptx"]:
            return self._generate_file_output(topic, format, ...)
        else:
            return self._generate_text_output(topic, ...)
```

### Phase 2: Test All Skills (PDF, XLSX, DOCX, PPTX) 🔄

Create integration tests for each skill type (see test suite plan).

### Phase 3: Integrate with work_outputs 🔜

Update work_executor to handle file outputs and store metadata.

### Phase 4: Optional Supabase Storage Persistence 🔜

Download files from Claude and upload to Supabase Storage for permanent retention.

---

## 9. References

- **Cookbooks**: [claude-cookbooks/skills](https://github.com/anthropics/claude-cookbooks/tree/b29ec6f109c0379fa2eb620611a3d504e28fba09/skills)
- **Official Docs**: [Agent Skills Overview](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- **Files API Docs**: [Files API](https://docs.claude.com/en/docs/build-with-claude/files)
- **YARNNN Docs**: [CLAUDE_SDK_CAPABILITIES.md](CLAUDE_SDK_CAPABILITIES.md), [WORK_OUTPUTS_ARCHITECTURE.md](WORK_OUTPUTS_ARCHITECTURE.md)

---

**Document Version**: 1.0.0
**Status**: Implementation-ready
**Next**: Apply migration + enable Skills in ReportingAgentSDK
# Work Output Lifecycle Implementation

**Status**: Implemented (Phase 1)
**Date**: 2025-11-17
**Commits**: 148144d7, 028d6143, d7cb97cb

## Executive Summary

Complete implementation of Work Output Lifecycle Management following the BFF (Backend-for-Frontend) pattern:
- Agents produce structured outputs via tool-use pattern
- Outputs are written to substrate-API for user supervision
- Clean separation between work-platform orchestration and substrate-api data ownership

## Architecture Overview

```
User Request
    ↓
work-platform (orchestrator)
    ├── Create work_session
    ├── Execute agent.deep_dive()
    │     ↓
    │   Claude API + emit_work_output tool
    │     ↓
    │   Parse structured outputs
    ├── Write outputs via BFF
    │     ↓
    │   substrate-API (data owner)
    │     ↓
    │   work_outputs table
    └── Update session status
    ↓
User Reviews Outputs
```

## Key Components

### 1. Database Schema (Supabase)

**work_outputs table** - Complete schema with:
- `basket_id`: Basket-scoped access (FK to baskets)
- `work_session_id`: Cross-DB reference (same Supabase, different domain)
- `output_type`: finding, recommendation, insight, draft_content, etc.
- `agent_type`: research, content, reporting
- `supervision_status`: pending_review → approved/rejected/revision_requested
- `confidence`: 0-1 confidence score
- `source_context_ids`: Provenance tracking (which blocks were used)
- `tool_call_id`: Claude's tool_use id for traceability

**Migrations Applied**:
- `20251117_work_outputs_recreate.sql` - Clean schema with RLS + GRANTS
- `20251117_work_outputs_functions.sql` - Helper functions (get_supervision_stats)

### 2. Tool-Use Pattern (work-platform/yarnnn_agents)

**Location**: `work-platform/api/src/yarnnn_agents/tools/`

```python
EMIT_WORK_OUTPUT_TOOL = {
    "name": "emit_work_output",
    "input_schema": {
        "properties": {
            "output_type": {"enum": ["finding", "recommendation", "insight", ...]},
            "title": {"type": "string", "maxLength": 200},
            "body": {
                "properties": {
                    "summary": {"type": "string"},
                    "details": {"type": "string"},
                    "evidence": {"type": "array"},
                    "recommendations": {"type": "array"},
                    "confidence_factors": {"type": "object"}
                },
                "required": ["summary"]
            },
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "source_block_ids": {"type": "array"}
        },
        "required": ["output_type", "title", "body", "confidence"]
    }
}
```

**Key Insight**: Forces Claude to emit structured outputs via `tool_choice`, ensuring machine-parseable deliverables with provenance tracking.

### 3. Agent Execution Flow (work-platform)

**Location**: `work-platform/api/src/app/routes/agent_orchestration.py`

```python
@router.post("/run")
async def run_agent_task(request, user):
    # 1. Check permissions (Phase 5 trial/subscription)
    # 2. Record work request
    # 3. Create work_session (NEW)
    work_session_id = await _create_work_session(...)

    # 4. Execute agent (returns work_outputs list)
    result = await _run_research_agent(request, user_id, work_session_id)

    # 5. Write outputs to substrate-API via BFF (NEW)
    work_outputs = result.get("work_outputs", [])
    output_write_result = write_agent_outputs(
        basket_id=request.basket_id,
        work_session_id=work_session_id,
        agent_type=request.agent_type,
        outputs=work_outputs,
    )

    # 6. Update session status
    await _update_work_session_status(work_session_id, "completed", output_count)
```

### 4. BFF Client (work-platform)

**Location**: `work-platform/api/src/clients/substrate_client.py`

Methods added:
- `create_work_output()` - Write single output
- `list_work_outputs()` - Query with filters
- `get_work_output()` - Get specific output
- `update_work_output_status()` - Approve/reject/revision
- `get_supervision_stats()` - Dashboard aggregation

**Auth Pattern**: Service-to-service via Bearer token + X-Service-Name header.

### 5. Substrate-API Routes

**Location**: `substrate-api/api/src/app/work_outputs/routes.py`

Endpoints (all under `/api/baskets/{basket_id}/work-outputs`):
- `POST /` - Create work output
- `GET /` - List with filters (supervision_status, agent_type, etc.)
- `GET /stats` - Supervision statistics
- `GET /{output_id}` - Get specific output
- `PATCH /{output_id}` - Update supervision status
- `DELETE /{output_id}` - Delete output

**Auth**: Supports both user JWT and service-to-service auth via `verify_user_or_service`.

### 6. Work-Platform Supervision Proxy

**Location**: `work-platform/api/src/app/routes/work_supervision.py`

**REWRITTEN** to use BFF pattern instead of direct DB access:
```python
@router.get("/baskets/{basket_id}/outputs")
async def list_outputs(basket_id, auth_info):
    client = get_substrate_client()
    return client.list_work_outputs(basket_id=basket_id, ...)

@router.post("/baskets/{basket_id}/outputs/{output_id}/approve")
async def approve_output(basket_id, output_id, request, auth_info):
    client = get_substrate_client()
    client.update_work_output_status(
        basket_id=basket_id,
        output_id=output_id,
        supervision_status="approved",
        reviewer_id=auth_info.get("user_id"),
    )
```

## Security Model

### RLS Policies (work_outputs table)

```sql
-- Users can view/create/update/delete outputs in their workspace baskets
USING (
    basket_id IN (
        SELECT b.id FROM baskets b
        JOIN workspace_memberships wm ON wm.workspace_id = b.workspace_id
        WHERE wm.user_id = auth.uid()
    )
)

-- Service role has full access
USING (auth.jwt()->>'role' = 'service_role')
```

### Service-to-Service Auth

**substrate-api/api/src/app/utils/service_auth.py**:
```python
def verify_user_or_service(request):
    # Check service auth first (ServiceToServiceAuthMiddleware)
    if hasattr(request.state, "service_name"):
        return {"service_name": ..., "is_service": True}

    # Then user JWT (AuthMiddleware)
    if hasattr(request.state, "user_id"):
        return {"user_id": ..., "is_service": False}

    raise HTTPException(401, "Authentication required")
```

## Data Flow Example

1. **User initiates research task**:
   ```json
   POST /agents/run
   {
     "agent_type": "research",
     "task_type": "deep_dive",
     "basket_id": "uuid",
     "parameters": {"topic": "competitor analysis"}
   }
   ```

2. **Agent executes** (uses emit_work_output tool):
   ```json
   {
     "output_type": "finding",
     "title": "Market Position Analysis",
     "body": {
       "summary": "Competitor X dominates 45% market share",
       "evidence": ["Source 1", "Source 2"],
       "recommendations": ["Focus on differentiation"]
     },
     "confidence": 0.85,
     "source_block_ids": ["block-uuid-1", "block-uuid-2"]
   }
   ```

3. **Outputs written to work_outputs** (via BFF):
   - supervision_status = "pending_review"
   - tool_call_id = Claude's tool_use id
   - source_context_ids = provenance tracking

4. **User reviews in supervision UI**:
   ```json
   POST /supervision/baskets/{basket_id}/outputs/{id}/approve
   {
     "notes": "Good analysis, incorporating into strategy"
   }
   ```

## Testing

### Local Testing

Use `test_research_agent.py` for local Claude API testing:
```bash
cd work-platform/api
python3 test_research_agent.py
```

### Integration Testing

After deployment:
1. Create basket/workspace
2. POST to `/agents/run` with research task
3. Check work_outputs table for pending_review entries
4. Verify outputs have proper structure and provenance

## Outstanding Items

1. **Deploy substrate-API to Render** - New routes need to be live
2. **Test tool-use with real Claude API** - Verify emit_work_output tool works
3. **Frontend supervision UI** - Build review interface
4. **Monitoring** - Add metrics for output approval rates, confidence calibration

## Files Modified

### New Files
- `supabase/migrations/20251117_work_outputs_recreate.sql`
- `supabase/migrations/20251117_work_outputs_functions.sql`
- `work-platform/api/src/yarnnn_agents/tools/__init__.py`
- `work-platform/api/src/yarnnn_agents/tools/work_output_tools.py`
- `work-platform/api/src/services/work_output_service.py`
- `substrate-api/api/src/app/work_outputs/__init__.py`
- `substrate-api/api/src/app/work_outputs/routes.py`
- `substrate-api/api/src/app/utils/service_auth.py`

### Modified Files
- `work-platform/api/src/yarnnn_agents/archetypes/research_agent.py` - Tool-use pattern
- `work-platform/api/src/yarnnn_agents/__init__.py` - Export tools
- `work-platform/api/src/clients/substrate_client.py` - BFF methods
- `work-platform/api/src/app/routes/agent_orchestration.py` - Session lifecycle + output writing
- `work-platform/api/src/app/routes/work_supervision.py` - **COMPLETE REWRITE** to BFF proxy
- `substrate-api/api/src/app/agent_server.py` - Router registration

## Key Design Decisions

1. **Tool-use pattern** - Forces structured outputs, enables provenance tracking
2. **BFF pattern** - work-platform orchestrates, substrate-api owns data
3. **Basket-scoped access** - RLS at basket level, not workspace level
4. **Cross-DB references** - work_session_id not FK-enforced (same DB, different domain)
5. **Dual auth support** - Both user JWT and service auth for flexibility
6. **Independent lifecycles** - Work supervision separate from substrate governance
