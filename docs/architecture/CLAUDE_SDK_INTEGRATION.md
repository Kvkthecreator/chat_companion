# Claude Agent SDK Integration

**Status:** Core SDK validated and operational (text-based workflows)
**Last Updated:** 2025-11-26

---

## Architecture Overview

### SDK Integration Stack

```
Python Application (FastAPI)
    ↓
claude-agent-sdk (Python package)
    ↓ wraps/spawns
Claude Code CLI (Node.js binary at /usr/bin/claude)
    ↓ loads
Skills (.claude/skills/) [OPTIONAL]
    ↓ generates
Files (PPTX, PDF, XLSX, DOCX)
```

### Critical Infrastructure Requirements

1. **Node.js 18.x** - Required for Claude Code CLI
2. **Claude Code CLI** - Must be installed globally via npm
3. **Python SDK** - `claude-agent-sdk>=0.1.8`
4. **Skills Directory** - `.claude/skills/` with SKILL.md files

**Dockerfile Installation:**
```dockerfile
# Install Node.js 18.x
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install Claude Code CLI globally (REQUIRED)
RUN npm install -g @anthropic-ai/claude-code && \
    which claude && \
    claude --version
```

---

## Message Structure & Parsing

### SDK Response Iterator

The SDK's `receive_response()` yields messages with this structure:

```python
SystemMessage
  └─ content: None

AssistantMessage  # Main message with content
  └─ content: List[ContentBlock]
      ├─ TextBlock(text="...")         # Has .text attribute
      ├─ ToolUseBlock(name="...", input={...})  # Has .name, .input
      └─ ToolResultBlock(...)

ResultMessage
  └─ content: None
```

### Text Extraction Pattern

**CRITICAL:** `TextBlock` objects do NOT have a `.type` attribute. They are typed by their Python class name.

**WRONG:**
```python
if block.type == 'text':  # ❌ .type doesn't exist
    text = block.text
```

**CORRECT:**
```python
# Check for .text attribute
if hasattr(block, 'text'):
    text += block.text

# Or use isinstance
from claude_agent_sdk import TextBlock
if isinstance(block, TextBlock):
    text += block.text
```

### Tool Detection Pattern

```python
async for message in client.receive_response():
    if hasattr(message, 'content') and isinstance(message.content, list):
        for block in message.content:
            # Text blocks
            if hasattr(block, 'text'):
                response_text += block.text

            # Tool invocations
            if hasattr(block, 'name'):  # ToolUseBlock
                tool_name = block.name
                tool_input = block.input
                # Handle tool invocation

            # Tool results
            if hasattr(block, 'tool_name'):  # ToolResultBlock
                result = block.result
                # Handle tool result
```

---

## MCP Tools Configuration

### Tool Naming Convention

MCP tools must use the pattern: `mcp__<server_name>__<tool_name>`

**Example:**
```python
from agents_sdk.shared_tools_mcp import create_shared_tools_server

# Create MCP server
shared_tools = create_shared_tools_server(
    basket_id=basket_id,
    work_ticket_id=work_ticket_id,
    agent_type="reporting",
    user_jwt=user_jwt
)

# Configure agent options
options = ClaudeAgentOptions(
    model="claude-sonnet-4-5",
    system_prompt="...",
    mcp_servers={"shared_tools": shared_tools},  # Server name
    allowed_tools=[
        "mcp__shared_tools__emit_work_output",  # Full tool path
        "TodoWrite",  # Built-in tools don't need prefix
    ]
)
```

### Shared Tools MCP Server

Located at: [shared_tools_mcp.py](../../work-platform/api/src/agents_sdk/shared_tools_mcp.py)

**Purpose:** Provides `emit_work_output` tool with context closure pattern

**Factory Pattern:**
```python
def create_shared_tools_server(
    basket_id: str,
    work_ticket_id: str,
    agent_type: str,
    user_jwt: Optional[str] = None
):
    """
    Creates MCP server where tools have access to context via closure.
    Eliminates need to pass context in every tool call.
    """
    @tool("emit_work_output", ...)
    async def emit_work_output_with_context(args: Dict[str, Any]):
        # basket_id, work_ticket_id available from closure
        ...

    return create_sdk_mcp_server(
        name="shared-agent-tools",
        tools=[emit_work_output_with_context]
    )
```

---

## Validated Core Capabilities

### ✅ Phase 1: Text Extraction

**Issue Fixed:** SDK was returning empty strings due to incorrect TextBlock parsing
**Root Cause:** Checking non-existent `.type` attribute
**Fix:** Changed to `if hasattr(block, 'text')` pattern

**Test Endpoint:** `/api/diagnostics/test-minimal-sdk`

**Validation Result:**
```json
{
  "status": "success",
  "message_count": 3,
  "response_text": "Hello! 👋\n\n1\n2\n3",
  "response_length": 15
}
```

### ✅ Phase 2: TodoWrite Tool

**Purpose:** Real-time progress tracking for user visibility
**Test Endpoint:** `/api/diagnostics/test-todowrite`

**Validation Result:**
```json
{
  "status": "success",
  "todowrite_invoked": true,
  "tool_calls": [{
    "tool": "TodoWrite",
    "input": {
      "todos": [
        {"content": "Create forms", "status": "pending", "activeForm": "Creating forms"},
        {"content": "Add auth", "status": "pending", "activeForm": "Adding auth"}
      ]
    }
  }]
}
```

### ✅ Phase 3: emit_work_output Tool

**Purpose:** Save agent outputs to database
**Test Endpoint:** `/api/diagnostics/test-emit-work-output`

**Validation Result:**
```json
{
  "status": "success",
  "emit_invoked": true,
  "tool_calls": [{
    "tool": "mcp__shared_tools__emit_work_output",
    "input": {
      "output_type": "draft_content",
      "title": "Cloud Computing Summary",
      "body": {"summary": "..."},
      "confidence": 0.9,
      "source_block_ids": []
    }
  }]
}
```

### ✅ Production Verification

**Database Evidence:**
```
Work Ticket: cc004714-f001-4c21-ab97-4ffcd6f7996c
  Status: completed
  Created: 2025-11-25 00:54:30
  Completed: 2025-11-25 00:59:32
  Duration: ~5 minutes

Work Output: 2e9a407e-35e1-40aa-954d-6233516227d5
  Type: report_draft
  Title: Executive Summary Deck - YARNNN Work Platform Integration
  Method: text
  Body Length: 3,505 characters
  Created: 2025-11-25 00:59:21
```

**Conclusion:** End-to-end text-based workflow validated in production ✅

---

## Agent Configurations

### Research Agent
```python
allowed_tools=[
    "mcp__shared_tools__emit_work_output",
    "web_search"
]
```

### Content Agent
```python
allowed_tools=["mcp__shared_tools__emit_work_output"]
agents=subagents  # Hierarchical agent support
```

### Reporting Agent
```python
allowed_tools=[
    "mcp__shared_tools__emit_work_output",
    "Skill",  # For PPTX/PDF generation
    "code_execution",
    "TodoWrite"
],
setting_sources=["user", "project"]  # Required for Skills
```

---

## Known Issues & Status

### ❌ Skills (PPTX/PDF Generation)

**Status:** Non-functional in server environments
**Root Cause:** Unknown - CLI installed correctly but Skills not invoking

**Evidence:**
- Claude Code CLI installed at `/usr/bin/claude` ✅
- Skills present in `.claude/skills/` ✅
- Agent configuration correct ✅
- SDK iterator returns zero messages when Skills enabled ❌

**Investigation Deferred:** Core text workflows prioritized

**Hypothesis:**
- Skills may require interactive terminal (TTY)
- Server environments may not support Skills
- Alternative: Implement file generation with python-pptx, reportlab

---

## Diagnostic Endpoints

All public endpoints (no auth required):

### `/api/diagnostics/test-minimal-sdk`
Tests basic SDK text generation without tools

### `/api/diagnostics/test-todowrite`
Validates TodoWrite tool invocation

### `/api/diagnostics/test-emit-work-output`
Validates emit_work_output MCP tool with server configuration

### `/api/diagnostics/skills`
Checks Skills infrastructure and CLI installation

---

## Testing Strategy

### Layered Validation Approach

```
Layer 1: SDK text extraction          ✅ VALIDATED
Layer 2: TodoWrite tool               ✅ VALIDATED
Layer 3: emit_work_output tool        ✅ VALIDATED
Layer 4: End-to-end text workflow     ✅ VALIDATED
Layer 5: Skills (PPTX/PDF)            ⏸️ DEFERRED
```

**Philosophy:** Build confidence progressively, validate each layer before advancing

### Test Pattern

1. **Isolate capability** - Test ONE thing at a time
2. **Minimal configuration** - Remove all optional features
3. **Inspect structure** - Log actual object attributes
4. **Fix parsing** - Update code based on reality, not assumptions
5. **Validate end-to-end** - Test in production with real data

---

## Common Pitfalls

### 1. Assuming Anthropic API Structure
The SDK's message structure differs from the direct Anthropic API:
- API: `block.type == 'text'` ✅
- SDK: `hasattr(block, 'text')` ✅

### 2. Forgetting MCP Prefix
Custom tools must include MCP server prefix:
- ❌ `allowed_tools=["emit_work_output"]`
- ✅ `allowed_tools=["mcp__shared_tools__emit_work_output"]`

### 3. Missing CLI Installation
Python SDK does NOT bundle the CLI:
- ❌ Assuming automatic installation
- ✅ Explicit npm install in Dockerfile

### 4. Silent Failures
SDK may return empty responses without errors:
- ✅ Add comprehensive logging
- ✅ Track message counts vs output counts
- ✅ Log every content block type

---

## Production Deployment Checklist

- [ ] Node.js 18.x installed
- [ ] Claude Code CLI installed globally
- [ ] CLI verification in Dockerfile build
- [ ] `.claude/skills/` directory present (if using Skills)
- [ ] MCP servers configured correctly
- [ ] Tool names include proper prefixes
- [ ] Text extraction uses `hasattr(block, 'text')`
- [ ] Comprehensive logging at INFO level
- [ ] Diagnostic endpoints accessible

---

## Future Considerations

### Alternative Approaches

**Option A: Direct Anthropic API**
- Pros: No CLI dependency, known to work
- Cons: No Skills support, manual tool execution

**Option B: Custom File Generation**
- Pros: Full control, works anywhere
- Cons: More code to maintain, loses Skills abstraction

**Option C: Hybrid Approach**
- Text generation via SDK (working)
- File generation via python-pptx, reportlab (custom)
- Best of both worlds

---

## References

- [Claude Agent SDK Docs](https://github.com/anthropics/claude-agent-sdk)
- [Shared Tools MCP Implementation](../../work-platform/api/src/agents_sdk/shared_tools_mcp.py)
- [Diagnostic Endpoints](../../work-platform/api/src/app/routes/diagnostics.py)
