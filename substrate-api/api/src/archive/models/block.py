from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

block_state = Literal[
    "PROPOSED",
    "ACCEPTED",
    "LOCKED",
    "CONSTANT",
    "SUPERSEDED",
    "REJECTED",
]


class Block(BaseModel):
    id: UUID
    basket_id: UUID | None = None
    parent_block_id: UUID | None = None
    semantic_type: str
    content: str | None = None
    version: int
    state: block_state
    scope: str | None = None
    canonical_value: str | None = None
    origin_ref: UUID | None = None
    created_at: datetime
