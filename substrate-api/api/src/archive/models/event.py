from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel

class Event(BaseModel):
    id: UUID
    basket_id: Optional[UUID] = None
    block_id: Optional[UUID] = None
    kind: Optional[str] = None
    payload: Optional[dict] = None
    ts: datetime
