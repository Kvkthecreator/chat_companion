#!/usr/bin/env python3
"""
Token Usage Measurement Script

Measures the actual token counts for system prompts and context injection
to identify optimization opportunities.
"""

import sys
sys.path.insert(0, 'src')

# Approximate token count (Claude uses ~4 chars per token on average)
def count_tokens(text: str) -> int:
    """Rough token estimate - actual tokenizer would be more accurate."""
    return len(text) // 4

def count_tokens_precise(text: str) -> dict:
    """Return both char count and estimated tokens."""
    chars = len(text)
    return {
        "chars": chars,
        "tokens_estimate": chars // 4,
        "tokens_conservative": chars // 3,  # More conservative estimate
    }

print("=" * 80)
print("YARNNN TOKEN USAGE AUDIT")
print("=" * 80)

# ============================================================================
# 1. ORCHESTRATION PATTERNS (Shared across all agents)
# ============================================================================
print("\n" + "=" * 80)
print("1. SHARED ORCHESTRATION PATTERNS")
print("=" * 80)

orchestration_content = open('src/agents_sdk/orchestration_patterns.py').read()

# Extract the actual string constants
import re

# Find YARNNN_ORCHESTRATION_PATTERNS
match = re.search(r'YARNNN_ORCHESTRATION_PATTERNS = """(.+?)"""', orchestration_content, re.DOTALL)
if match:
    orch_patterns = match.group(1)
    stats = count_tokens_precise(orch_patterns)
    print(f"\nYARNNN_ORCHESTRATION_PATTERNS:")
    print(f"  Characters: {stats['chars']:,}")
    print(f"  Tokens (est): {stats['tokens_estimate']:,}")
    print(f"  Tokens (conservative): {stats['tokens_conservative']:,}")

# Find TOOL_CALLING_GUIDANCE
match = re.search(r'TOOL_CALLING_GUIDANCE = """(.+?)"""', orchestration_content, re.DOTALL)
if match:
    tool_guidance = match.group(1)
    stats = count_tokens_precise(tool_guidance)
    print(f"\nTOOL_CALLING_GUIDANCE:")
    print(f"  Characters: {stats['chars']:,}")
    print(f"  Tokens (est): {stats['tokens_estimate']:,}")

# ============================================================================
# 2. RESEARCH AGENT SYSTEM PROMPT
# ============================================================================
print("\n" + "=" * 80)
print("2. RESEARCH AGENT SYSTEM PROMPT")
print("=" * 80)

research_content = open('src/agents_sdk/research_agent_sdk.py').read()

# Find RESEARCH_AGENT_SYSTEM_PROMPT
match = re.search(r'RESEARCH_AGENT_SYSTEM_PROMPT = """(.+?)"""', research_content, re.DOTALL)
if match:
    research_prompt = match.group(1)
    stats = count_tokens_precise(research_prompt)
    print(f"\nRESEARCH_AGENT_SYSTEM_PROMPT (base):")
    print(f"  Characters: {stats['chars']:,}")
    print(f"  Tokens (est): {stats['tokens_estimate']:,}")

# Simulate the full system prompt build
print("\n--- Simulating full system prompt build ---")

# These are approximations of what _build_static_system_prompt() adds
agent_identity = """# Research Agent Identity

You are YARNNN's specialized Research Agent for intelligence gathering and analysis.

**Your Role**: Conduct comprehensive research, gather intelligence, and produce structured findings.

**Monitoring Domains**: general"""

available_tools = """## Tools You Have Access To

1. **emit_work_output** (mcp__shared_tools__emit_work_output)
   - CRITICAL: Use this to save all findings, insights, recommendations
   - Required fields: output_type, title, body, confidence, metadata, source_block_ids
   - Example: emit_work_output(output_type="finding", title="Competitor X pricing", ...)

2. **WebSearch** (built-in)
   - Search the web for current information
   - Use for live data, news, market information
   - Complements substrate (historical) with real-time data

3. **TodoWrite** (for progress tracking)
   - Use for multi-step research workflows
   - Helps user see real-time progress"""

quality_standards = """## Research Quality Standards

**Accuracy First**:
- Verify information from multiple sources when possible
- Assign confidence scores based on evidence quality
- Flag uncertainty explicitly (don't guess)

**Contextual Awareness**:
- Query substrate via substrate.query() before starting research
- Check what's already known (avoid redundant research)
- Reference source_block_ids in emit_work_output for provenance
- Use on-demand queries for efficiency (fetch only relevant context)"""

# Calculate totals
components = {
    "Agent Identity": agent_identity,
    "Agent Responsibilities (RESEARCH_AGENT_SYSTEM_PROMPT)": research_prompt if match else "",
    "YARNNN_ORCHESTRATION_PATTERNS": orch_patterns if 'orch_patterns' in dir() else "",
    "TOOL_CALLING_GUIDANCE": tool_guidance if 'tool_guidance' in dir() else "",
    "Available Tools": available_tools,
    "Quality Standards": quality_standards,
}

total_chars = 0
total_tokens = 0
print("\nComponent Breakdown:")
print("-" * 60)
for name, content in components.items():
    chars = len(content)
    tokens = chars // 4
    total_chars += chars
    total_tokens += tokens
    print(f"{name}:")
    print(f"  {chars:,} chars / ~{tokens:,} tokens")

print("-" * 60)
print(f"TOTAL RESEARCH SYSTEM PROMPT:")
print(f"  {total_chars:,} chars / ~{total_tokens:,} tokens")

# ============================================================================
# 3. CONTENT AGENT SYSTEM PROMPT
# ============================================================================
print("\n" + "=" * 80)
print("3. CONTENT AGENT SYSTEM PROMPT")
print("=" * 80)

content_agent = open('src/agents_sdk/content_agent_sdk.py').read()

# Find all the specialist prompts
specialists = [
    ("CONTENT_AGENT_SYSTEM_PROMPT", r'CONTENT_AGENT_SYSTEM_PROMPT = """(.+?)"""'),
    ("TWITTER_SPECIALIST", r'TWITTER_SPECIALIST = """(.+?)"""'),
    ("LINKEDIN_SPECIALIST", r'LINKEDIN_SPECIALIST = """(.+?)"""'),
    ("BLOG_SPECIALIST", r'BLOG_SPECIALIST = """(.+?)"""'),
    ("INSTAGRAM_SPECIALIST", r'INSTAGRAM_SPECIALIST = """(.+?)"""'),
]

content_total = 0
for name, pattern in specialists:
    match = re.search(pattern, content_agent, re.DOTALL)
    if match:
        text = match.group(1)
        chars = len(text)
        tokens = chars // 4
        content_total += chars
        print(f"\n{name}:")
        print(f"  {chars:,} chars / ~{tokens:,} tokens")

# Add shared components
shared_total = len(orch_patterns) + len(tool_guidance) if 'orch_patterns' in dir() else 0
content_total += shared_total

print(f"\n+ Shared components (orchestration + tools): ~{shared_total:,} chars")
print("-" * 60)
print(f"TOTAL CONTENT SYSTEM PROMPT: ~{content_total:,} chars / ~{content_total//4:,} tokens")

# ============================================================================
# 4. REPORTING AGENT SYSTEM PROMPT
# ============================================================================
print("\n" + "=" * 80)
print("4. REPORTING AGENT SYSTEM PROMPT")
print("=" * 80)

reporting_content = open('src/agents_sdk/reporting_agent_sdk.py').read()

match = re.search(r'REPORTING_AGENT_SYSTEM_PROMPT = """(.+?)"""', reporting_content, re.DOTALL)
if match:
    reporting_prompt = match.group(1)
    stats = count_tokens_precise(reporting_prompt)
    print(f"\nREPORTING_AGENT_SYSTEM_PROMPT (base):")
    print(f"  Characters: {stats['chars']:,}")
    print(f"  Tokens (est): {stats['tokens_estimate']:,}")

    reporting_total = stats['chars'] + shared_total
    print(f"\n+ Shared components: ~{shared_total:,} chars")
    print("-" * 60)
    print(f"TOTAL REPORTING SYSTEM PROMPT: ~{reporting_total:,} chars / ~{reporting_total//4:,} tokens")

# ============================================================================
# 5. USER MESSAGE CONTEXT (Research deep_dive)
# ============================================================================
print("\n" + "=" * 80)
print("5. USER MESSAGE TEMPLATE (Research deep_dive)")
print("=" * 80)

# This is the template from research_agent_sdk.py lines 307-335
user_message_template = '''Conduct comprehensive research on: {topic}

**Pre-loaded Context:** {context_summary}
**Source Block IDs:** {source_block_ids if source_block_ids else 'none'}

**Research Objectives:**
1. Provide comprehensive overview
2. Identify key trends and patterns
3. Analyze implications
4. Generate actionable insights

**CRITICAL INSTRUCTION:**
You MUST use the emit_work_output tool to record your findings. Do NOT just describe findings in text.

For each significant finding, insight, or recommendation you discover:
1. Call emit_work_output with structured data
2. Use appropriate output_type (finding, recommendation, insight)
3. Include source_block_ids from the context blocks used: {source_block_ids}
4. Assign confidence scores based on evidence quality

Example workflow:
- Find a key fact → emit_work_output(output_type="finding", ...)
- Identify a pattern → emit_work_output(output_type="insight", ...)
- Suggest action → emit_work_output(output_type="recommendation", ...)

You may emit multiple outputs. Each will be reviewed by the user.

Please conduct thorough research and synthesis, emitting structured outputs for all significant findings.'''

stats = count_tokens_precise(user_message_template)
print(f"\nUser message template (without context):")
print(f"  Characters: {stats['chars']:,}")
print(f"  Tokens (est): {stats['tokens_estimate']:,}")

# ============================================================================
# 6. SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SUMMARY: EXPECTED INPUT TOKENS PER REQUEST")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────┐
│ Component                              │ Tokens (est)           │
├─────────────────────────────────────────────────────────────────┤
│ Research System Prompt                 │ ~{:,}                │
│ User Message Template                  │ ~{:,}                  │
│ Substrate Context (10 blocks @ 50 ea)  │ ~500                   │
│ Topic + Parameters                     │ ~50-200                │
├─────────────────────────────────────────────────────────────────┤
│ EXPECTED FIRST REQUEST TOTAL           │ ~{:,}              │
│                                                                 │
│ YOUR ACTUAL (from logs)                │ 23,000-27,000          │
│                                                                 │
│ GAP TO INVESTIGATE                     │ ~{:,}+             │
└─────────────────────────────────────────────────────────────────┘
""".format(
    total_tokens,
    stats['tokens_estimate'],
    total_tokens + stats['tokens_estimate'] + 500 + 100,
    23000 - (total_tokens + stats['tokens_estimate'] + 500 + 100)
))

print("\nPossible sources of the gap:")
print("1. Conversation history from resumed sessions")
print("2. MCP tool definitions (emit_work_output schema)")
print("3. WebSearch tool definition and results")
print("4. Claude SDK internal overhead")
print("5. Substrate blocks larger than estimated")
