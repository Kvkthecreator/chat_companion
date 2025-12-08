from typing import List
from .types import RawDumpChunk

def chunk_text(text: str, max_len: int = 6000) -> List[RawDumpChunk]:
    if not text:
        return []
    chunks, cur, total = [], [], 0
    for para in text.split("\n\n"):
        if total + len(para) > max_len and cur:
            chunks.append(RawDumpChunk(text="\n\n".join(cur), order_index=len(chunks)))
            cur, total = [], 0
        cur.append(para); total += len(para) + 2
    if cur:
        chunks.append(RawDumpChunk(text="\n\n".join(cur), order_index=len(chunks)))
    return chunks