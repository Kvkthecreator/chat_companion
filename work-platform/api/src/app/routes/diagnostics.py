"""
Diagnostic endpoints for troubleshooting agent execution.

Post-SDK removal: Tests updated to use direct Anthropic API.
"""

import os
import logging
from fastapi import APIRouter
from pathlib import Path

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])
logger = logging.getLogger(__name__)


@router.get("/skills")
async def check_skills_availability():
    """
    Check if Skills are accessible at runtime.

    Returns:
        - working_directory: Current working directory
        - claude_dir_exists: Whether .claude directory exists
        - skills_dir_exists: Whether .claude/skills exists
        - available_skills: List of installed Skills
    """
    cwd = os.getcwd()
    claude_dir = Path(cwd) / ".claude"
    skills_dir = claude_dir / "skills"

    result = {
        "working_directory": cwd,
        "claude_dir_exists": claude_dir.exists(),
        "claude_dir_path": str(claude_dir),
        "skills_dir_exists": skills_dir.exists(),
        "skills_dir_path": str(skills_dir),
        "available_skills": [],
        "skill_details": {}
    }

    if skills_dir.exists():
        skill_dirs = [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        result["available_skills"] = [d.name for d in skill_dirs]

        for skill_dir in skill_dirs:
            skill_name = skill_dir.name
            skill_md = skill_dir / "SKILL.md"

            result["skill_details"][skill_name] = {
                "directory_exists": True,
                "skill_md_exists": skill_md.exists(),
                "skill_md_path": str(skill_md),
                "skill_md_size": skill_md.stat().st_size if skill_md.exists() else 0,
                "files": [f.name for f in skill_dir.iterdir() if f.is_file()][:10]
            }

    result["environment"] = {
        "PYTHONPATH": os.getenv("PYTHONPATH"),
        "PATH": os.getenv("PATH", "")[:200] + "...",
        "HOME": os.getenv("HOME"),
        "USER": os.getenv("USER"),
        "ANTHROPIC_API_KEY": "***" + os.getenv("ANTHROPIC_API_KEY", "NOT_SET")[-4:] if os.getenv("ANTHROPIC_API_KEY") else "NOT_SET",
    }

    result["sdk_status"] = {
        "status": "removed",
        "note": "Claude Agent SDK removed in favor of direct Anthropic API"
    }

    logger.info(f"Skills diagnostic: {len(result['available_skills'])} skills found")

    return result


@router.get("/agent-config")
async def check_agent_configuration():
    """
    Check agent configuration.

    Returns info about how agents are configured (post-SDK removal).
    """
    return {
        "status": "migrated",
        "architecture": "direct_anthropic_api",
        "note": "Claude Agent SDK removed. Agents now use AnthropicDirectClient.",
        "available_executors": [
            {
                "name": "ResearchExecutor",
                "path": "agents/research_executor.py",
                "status": "active"
            },
            {
                "name": "ContentExecutor",
                "path": "agents/content_executor.py",
                "status": "pending_migration"
            },
            {
                "name": "ReportingExecutor",
                "path": "agents/reporting_executor.py",
                "status": "pending_migration"
            }
        ],
        "tools": [
            "emit_work_output (via substrate-API HTTP)",
            "web_search (planned)"
        ]
    }


@router.post("/test-direct-api")
async def test_direct_api():
    """
    Test direct Anthropic API functionality.

    This validates:
    1. Anthropic API key is configured
    2. Direct API calls work
    3. Basic message completion succeeds

    Returns basic response info.
    """
    print("[DIRECT API TEST] Starting...", flush=True)

    try:
        from clients.anthropic_client import AnthropicDirectClient

        client = AnthropicDirectClient()

        print("[DIRECT API TEST] Sending simple prompt...", flush=True)
        result = await client.execute(
            system_prompt="You are a helpful assistant. Respond concisely.",
            user_message="Say hello and count to 3.",
            tools=[],  # No tools, just basic chat
        )

        print(f"[DIRECT API TEST] Complete: {len(result.response_text)} chars", flush=True)

        return {
            "status": "success",
            "response_text": result.response_text,
            "response_length": len(result.response_text),
            "token_usage": {
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cache_read_tokens": result.cache_read_tokens,
            },
            "model": result.model,
            "stop_reason": result.stop_reason
        }

    except Exception as e:
        print(f"[DIRECT API TEST] FAILED: {e}", flush=True)
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/test-emit-work-output")
async def test_emit_work_output():
    """
    Test emit_work_output tool via direct API.

    This validates:
    1. Direct API accepts tool definitions
    2. Agent invokes emit_work_output
    3. Tool execution via substrate-API HTTP works

    Returns tool invocation details.
    """
    from app.utils.supabase_client import supabase_admin_client as supabase

    print("[EMIT TEST] Starting...", flush=True)

    try:
        from clients.anthropic_client import AnthropicDirectClient

        # Get a valid basket and work_ticket
        production_basket_id = "4eccb9a0-9fe4-4660-861e-b80a75a20824"

        work_ticket_result = supabase.table("work_tickets") \
            .select("id") \
            .eq("basket_id", production_basket_id) \
            .limit(1) \
            .execute()

        if not work_ticket_result.data:
            return {
                "status": "error",
                "error": "No work_tickets found in production basket",
                "basket_id": production_basket_id
            }

        work_ticket_id = work_ticket_result.data[0]["id"]
        print(f"[EMIT TEST] Using basket={production_basket_id}, work_ticket={work_ticket_id}", flush=True)

        client = AnthropicDirectClient()

        tool_context = {
            "basket_id": production_basket_id,
            "work_ticket_id": work_ticket_id,
            "agent_type": "research",
        }

        print("[EMIT TEST] Sending prompt with emit_work_output tool...", flush=True)
        result = await client.execute(
            system_prompt="""You are a research assistant. When you have a finding, you MUST use the emit_work_output tool to save it.

CRITICAL: After writing any content, use emit_work_output to save your work.

Required parameters:
- output_type: "finding" or "insight"
- title: Clear title
- body: Dictionary with at least "summary" key
- confidence: Number between 0 and 1
- source_block_ids: List of source IDs (can be empty list [])""",
            user_message="Write a brief 1-sentence summary about AI assistants and save it using the emit_work_output tool.",
            tools=["emit_work_output"],
            tool_context=tool_context,
        )

        emit_invoked = any(tc.name == "emit_work_output" for tc in result.tool_calls)

        return {
            "status": "success",
            "emit_invoked": emit_invoked,
            "tool_calls": [
                {"tool": tc.name, "input": str(tc.input)[:200]}
                for tc in result.tool_calls
            ],
            "work_outputs": result.work_outputs,
            "response_text": result.response_text[:500] if result.response_text else "(no text)",
            "token_usage": {
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            }
        }

    except Exception as e:
        print(f"[EMIT TEST] FAILED: {e}", flush=True)
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/test-research-workflow")
async def test_research_workflow():
    """
    Test research workflow with direct API.

    This validates:
    1. ResearchExecutor initialization
    2. Task execution
    3. emit_work_output invocation
    4. Token tracking

    Returns workflow execution details.
    """
    from app.utils.supabase_client import supabase_admin_client as supabase

    print("[RESEARCH TEST] Starting...", flush=True)

    try:
        from agents.research_executor import ResearchExecutor

        # Get a valid basket and work_ticket
        production_basket_id = "4eccb9a0-9fe4-4660-861e-b80a75a20824"

        work_ticket_result = supabase.table("work_tickets") \
            .select("id") \
            .eq("basket_id", production_basket_id) \
            .limit(1) \
            .execute()

        if not work_ticket_result.data:
            return {
                "status": "error",
                "error": "No work_tickets found",
                "basket_id": production_basket_id
            }

        work_ticket_id = work_ticket_result.data[0]["id"]
        print(f"[RESEARCH TEST] Using basket={production_basket_id}, work_ticket={work_ticket_id}", flush=True)

        # Create executor
        executor = ResearchExecutor(
            basket_id=production_basket_id,
            workspace_id="test-workspace",
            work_ticket_id=work_ticket_id,
            user_id="test-user",
        )

        print("[RESEARCH TEST] Executing research task...", flush=True)
        result = await executor.execute(
            task="What are the key benefits of AI assistants? Provide 2-3 findings.",
            research_scope="general",
            depth="quick",
        )

        return {
            "status": "success",
            "work_outputs_count": len(result.work_outputs),
            "work_outputs": result.work_outputs,
            "tool_calls_count": len(result.tool_calls),
            "response_length": len(result.response_text),
            "response_preview": result.response_text[:500] if result.response_text else "(no text)",
            "token_usage": {
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cache_read_tokens": result.cache_read_tokens,
            },
            "model": result.model,
            "stop_reason": result.stop_reason
        }

    except Exception as e:
        print(f"[RESEARCH TEST] FAILED: {e}", flush=True)
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/migration-status")
async def get_migration_status():
    """
    Get SDK removal migration status.

    Returns comprehensive status of the migration from Claude Agent SDK
    to direct Anthropic API.
    """
    return {
        "migration": "sdk_removal",
        "recovery_tag": "pre-sdk-removal",
        "status": "phase_1_complete",
        "phases": {
            "phase_1": {
                "name": "Foundation",
                "status": "complete",
                "deliverables": [
                    "AnthropicDirectClient created",
                    "BaseAgentExecutor created",
                    "ResearchExecutor implemented",
                    "agents_sdk/ deleted",
                    "Node.js removed from Dockerfile",
                    "claude-agent-sdk removed from requirements"
                ]
            },
            "phase_2": {
                "name": "Agent Executors",
                "status": "pending",
                "deliverables": [
                    "ContentExecutor",
                    "ReportingExecutor",
                    "ThinkingPartnerExecutor"
                ]
            },
            "phase_3": {
                "name": "Work Output Promotion",
                "status": "pending",
                "deliverables": [
                    "PromotionService",
                    "Archive/Asset/Substrate paths"
                ]
            },
            "phase_4": {
                "name": "P4 Context Snapshot",
                "status": "pending",
                "deliverables": [
                    "BasketSnapshotService",
                    "Mutation triggers"
                ]
            }
        },
        "active_endpoints": {
            "/api/work/research/execute": "active",
            "/api/work/reporting/execute": "pending_migration",
            "/api/tp/chat": "limited_functionality"
        }
    }
