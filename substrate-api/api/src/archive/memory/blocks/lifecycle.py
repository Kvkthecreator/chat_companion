# ruff: noqa
"""Block lifecycle enforcement and state transition validation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Set
from uuid import UUID, uuid4

from fastapi import HTTPException
from pydantic import BaseModel

from ...models.block import block_state
from ...utils.db import as_json
from ...utils.supabase_client import supabase_client as supabase


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class BlockLifecycleService:
    """Handles block state transitions and lifecycle enforcement."""

    # Valid state transitions based on canonical memory model
    VALID_TRANSITIONS: Dict[str, Set[str]] = {
        "PROPOSED": {"ACCEPTED", "REJECTED"},
        "ACCEPTED": {"LOCKED", "SUPERSEDED"},
        "LOCKED": {"CONSTANT", "SUPERSEDED"},
        "CONSTANT": set(),  # Terminal state
        "SUPERSEDED": set(),  # Terminal state
        "REJECTED": set(),  # Terminal state
    }

    # States that can only be set by users (not agents)
    USER_ONLY_STATES = {"ACCEPTED", "LOCKED", "CONSTANT", "REJECTED"}

    # States that agents can propose
    AGENT_PROPOSABLE_STATES = {"PROPOSED", "SUPERSEDED"}

    @classmethod
    def validate_transition(
        cls,
        from_state: str,
        to_state: str,
        actor_type: str = "user"
    ) -> None:
        """Validate that a state transition is allowed."""
        if from_state not in cls.VALID_TRANSITIONS:
            raise StateTransitionError(f"Invalid current state: {from_state}")

        if to_state not in cls.VALID_TRANSITIONS[from_state]:
            raise StateTransitionError(
                f"Cannot transition from {from_state} to {to_state}. "
                f"Valid transitions: {cls.VALID_TRANSITIONS[from_state]}"
            )

        # Enforce user-only state restrictions
        if actor_type == "agent" and to_state in cls.USER_ONLY_STATES:
            raise StateTransitionError(
                f"Agents cannot set state to {to_state}. Only users can accept/lock blocks."
            )

    @classmethod
    def can_modify_content(cls, state: str, actor_type: str = "user") -> bool:
        """Check if content can be modified in the given state."""
        if state in {"LOCKED", "CONSTANT"}:
            return False
        if state == "REJECTED":
            return False
        if actor_type == "agent" and state != "PROPOSED":
            return False
        return True

    @classmethod
    async def transition_block_state(
        cls,
        block_id: UUID,
        new_state: str,
        actor_id: str,
        actor_type: str = "user",
        reason: Optional[str] = None
    ) -> Dict:
        """Perform a validated state transition with audit trail."""

        # Get current block state
        current_resp = (
            supabase.table("blocks")
            .select("id,state,version,workspace_id,basket_id")
            .eq("id", str(block_id))
            .maybe_single()
            .execute()
        )

        if not current_resp.data:
            raise HTTPException(404, "Block not found")

        current_block = current_resp.data
        current_state = current_block["state"]

        # Validate transition
        cls.validate_transition(current_state, new_state, actor_type)

        # Create revision record via RPC
        diff_json = {
            "state": {"from": current_state, "to": new_state},
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
        rev_resp = supabase.rpc('fn_block_revision_create', {
            "p_basket_id": current_block["basket_id"],
            "p_block_id": str(block_id),
            "p_workspace_id": current_block["workspace_id"],
            "p_summary": f"State transition: {current_state} → {new_state}",
            "p_diff_json": diff_json,
        }).execute()
        revision_id = rev_resp.data

        # Update block state and increment version
        update_resp = (
            supabase.table("blocks")
            .update({
                "state": new_state,
                "version": current_block["version"] + 1,
                "updated_at": datetime.utcnow().isoformat()
            })
            .eq("id", str(block_id))
            .execute()
        )

        # Create event
        event_data = {
            "id": str(uuid4()),
            "basket_id": current_block.get("basket_id"),
            "block_id": str(block_id),
            "kind": "block.state_changed",
            "payload": {
                "from_state": current_state,
                "to_state": new_state,
                "actor_id": actor_id,
                "actor_type": actor_type,
                "revision_id": revision_id
            }
        }

        supabase.table("events").insert(as_json(event_data)).execute()

        return update_resp.data[0] if update_resp.data else {}


class BlockProposalService:
    """Handles agent block proposals and user approval workflow."""

    @classmethod
    async def propose_block(
        cls,
        basket_id: UUID,
        semantic_type: str,
        content: str,
        agent_id: str,
        origin_ref: Optional[UUID] = None,
        scope: Optional[str] = None
    ) -> Dict:
        """Create a new block in PROPOSED state from agent."""

        # Get workspace_id from basket
        basket_resp = (
            supabase.table("baskets")
            .select("workspace_id")
            .eq("id", str(basket_id))
            .maybe_single()
            .execute()
        )

        workspace_id = basket_resp.data.get("workspace_id") if basket_resp.data else None

        # Insert block via RPC
        insert_resp = supabase.rpc('fn_block_create', {
            "p_basket_id": str(basket_id),
            "p_workspace_id": workspace_id,
            "p_title": semantic_type,
            "p_body_md": content,
        }).execute()
        block_id = insert_resp.data

        # Create proposal event
        event_data = {
            "id": str(uuid4()),
            "basket_id": str(basket_id),
            "block_id": str(block_id),
            "kind": "block.proposed",
            "payload": {
                "agent_id": agent_id,
                "semantic_type": semantic_type,
                "origin_ref": str(origin_ref) if origin_ref else None,
            },
        }

        supabase.table("events").insert(as_json(event_data)).execute()

        block_resp = (
            supabase.table("blocks")
            .select("*")
            .eq("id", str(block_id))
            .maybe_single()
            .execute()
        )

        return block_resp.data if block_resp.data else {"id": block_id}

    @classmethod
    async def approve_proposal(
        cls,
        block_id: UUID,
        user_id: str,
        feedback: Optional[str] = None
    ) -> Dict:
        """User approves a proposed block."""
        return await BlockLifecycleService.transition_block_state(
            block_id=block_id,
            new_state="ACCEPTED",
            actor_id=user_id,
            actor_type="user",
            reason=f"User approval: {feedback}" if feedback else "User approval"
        )

    @classmethod
    async def reject_proposal(
        cls,
        block_id: UUID,
        user_id: str,
        reason: Optional[str] = None
    ) -> Dict:
        """User rejects a proposed block."""
        return await BlockLifecycleService.transition_block_state(
            block_id=block_id,
            new_state="REJECTED",
            actor_id=user_id,
            actor_type="user",
            reason=f"User rejection: {reason}" if reason else "User rejection"
        )


# Request/Response models for API endpoints
class StateTransitionRequest(BaseModel):
    new_state: block_state
    reason: Optional[str] = None

class BlockProposalRequest(BaseModel):
    semantic_type: str
    content: str
    origin_ref: Optional[UUID] = None
    scope: Optional[str] = None

class ProposalActionRequest(BaseModel):
    feedback: Optional[str] = None
