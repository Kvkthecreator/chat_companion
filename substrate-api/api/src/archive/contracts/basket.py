from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Union

class SourceRawDump(BaseModel):
    type: Literal["raw_dump"]
    id: str

class SourceText(BaseModel):
    type: Literal["text"]
    content: str

class SourceFile(BaseModel):
    type: Literal["file"]
    id: str
    mime: Optional[str] = None

Source = Union[SourceRawDump, SourceText, SourceFile]

class BasketChangeRequest(BaseModel):
    request_id: str
    basket_id: str
    intent: Optional[str] = None
    sources: Optional[List[Source]] = None
    agent_hints: Optional[List[str]] = None
    user_context: Optional[Dict[str, Any]] = None

class EntityChangeBlock(BaseModel):
    entity: Literal["context_block"]
    id: str
    from_version: Optional[int] = None
    to_version: Optional[int] = None
    diff: Optional[str] = None

class EntityChangeTask(BaseModel):
    entity: Literal["task"]
    id: str
    op: Literal["CREATE","UPDATE","DELETE"]
    payload: Optional[Dict[str, Any]] = None

class EntityChangeDocument(BaseModel):
    entity: Literal["document"]
    id: str
    from_version: Optional[int] = None
    to_version: Optional[int] = None
    diff: Optional[str] = None

EntityChange = Union[EntityChangeBlock, EntityChangeTask, EntityChangeDocument]

class RecommendedAction(BaseModel):
    type: Literal["APPLY_ALL","EDIT","RUN_AGENT"]
    target: Optional[Literal["context_block","task","document"]] = None
    id: Optional[str] = None
    args: Optional[Dict[str, Any]] = None

class BasketDelta(BaseModel):
    delta_id: str
    basket_id: str
    summary: str
    changes: List[EntityChange]
    recommended_actions: Optional[List[RecommendedAction]] = None
    explanations: Optional[List[Dict[str, str]]] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    created_at: str
