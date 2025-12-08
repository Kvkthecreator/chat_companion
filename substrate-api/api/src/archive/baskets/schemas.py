from typing import Literal, Optional, Union

from pydantic import BaseModel, Field

# Work Mode Types
WorkMode = Literal["init_build", "evolve_turn"]

class SourceRawDump(BaseModel):
    type: Literal["raw_dump"]
    id: str

class SourceText(BaseModel):
    type: Literal["text"]
    text: str

Source = Union[SourceRawDump, SourceText]

class WorkPolicy(BaseModel):
    allow_structural_changes: bool = True
    preserve_blocks: list[str] = []
    update_document_ids: list[str] = []
    strict_link_provenance: bool = True

class WorkOptions(BaseModel):
    fast: bool = False
    max_tokens: int = 8000
    trace_req_id: Optional[str] = None

class BasketWorkRequest(BaseModel):
    mode: WorkMode
    # Require at least one source to avoid undefined work requests
    sources: list[Source] = Field(..., min_length=1)
    policy: WorkPolicy = WorkPolicy()
    options: WorkOptions = WorkOptions()

class BasketInput(BaseModel):
    name: Optional[str] = None


class CreateBasketReq(BaseModel):
    """DTO matching the CreateBasketReq contract."""

    idempotency_key: str
    basket: BasketInput
