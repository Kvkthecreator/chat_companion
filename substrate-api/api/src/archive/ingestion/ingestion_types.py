from pydantic import BaseModel
from typing import List, Optional

class ParseResult(BaseModel):
    text: str
    ref_only: bool = False  # true when no text extracted (e.g., scanned pdf)

class RawDumpChunk(BaseModel):
    text: str
    order_index: int
    source_name: Optional[str] = None