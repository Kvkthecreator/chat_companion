"""Health check endpoints."""
from fastapi import APIRouter, Depends
from app.deps import get_db

router = APIRouter()


@router.get("/health")
async def health():
    """Basic health check."""
    return {"status": "healthy", "service": "clearinghouse-api"}


@router.get("/health/db")
async def health_db():
    """Database connectivity check."""
    try:
        db = await get_db()
        result = await db.fetch_one("SELECT 1 as ok")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}


@router.get("/health/tables")
async def health_tables():
    """Check that core tables exist."""
    try:
        db = await get_db()
        tables = await db.fetch_all("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        table_names = [t["table_name"] for t in tables]

        required_tables = [
            "workspaces", "workspace_memberships", "catalogs",
            "rights_schemas", "rights_entities", "reference_assets",
            "proposals", "proposal_comments", "governance_rules",
            "license_templates", "licensees", "license_grants", "usage_records",
            "timeline_events"
        ]

        missing = [t for t in required_tables if t not in table_names]

        return {
            "status": "healthy" if not missing else "degraded",
            "tables": table_names,
            "required_tables": required_tables,
            "missing_tables": missing,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.post("/health/migrate/session-states")
async def migrate_session_states():
    """One-time migration: Backfill session_state for existing sessions.

    This sets:
    - session_state = 'active' for sessions where is_active = TRUE and session_state IS NULL
    - session_state = 'complete' for sessions where is_active = FALSE and session_state IS NULL
    """
    try:
        db = await get_db()

        # Count before
        before = await db.fetch_one("""
            SELECT COUNT(*) as count FROM sessions WHERE session_state IS NULL
        """)

        # Backfill active sessions
        active_result = await db.execute("""
            UPDATE sessions SET session_state = 'active'
            WHERE session_state IS NULL AND is_active = TRUE
        """)

        # Backfill completed sessions
        complete_result = await db.execute("""
            UPDATE sessions SET session_state = 'complete'
            WHERE session_state IS NULL AND is_active = FALSE
        """)

        # Count after
        after = await db.fetch_one("""
            SELECT COUNT(*) as count FROM sessions WHERE session_state IS NULL
        """)

        # Get current distribution
        distribution = await db.fetch_all("""
            SELECT session_state, is_active, COUNT(*) as count
            FROM sessions
            GROUP BY session_state, is_active
            ORDER BY session_state
        """)

        return {
            "status": "success",
            "null_before": before["count"],
            "null_after": after["count"],
            "distribution": [dict(row) for row in distribution],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
