from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class RawDump(BaseModel):
    """Raw input text unit recorded for a document."""

    id: UUID
    basket_id: UUID
    document_id: Optional[UUID] = None
    body_md: Optional[str] = None
    created_at: datetime
    workspace_id: UUID
    file_url: Optional[str] = None
