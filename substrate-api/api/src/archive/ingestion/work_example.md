# Example: Dumps → Work Flow

After creating dumps via `/api/dumps/new`, the frontend can trigger work:

```bash
# Step 1: Create dump(s)
curl -X POST http://localhost:8000/api/dumps/new \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "basket_id": "123e4567-e89b-12d3-a456-426614174000",
    "text_dump": "Long document content here...",
    "file_url": "https://example.com/doc.pdf"
  }'

# Response (single dump):
# {"raw_dump_id": "abc123..."}

# Response (multiple chunks):
# {"raw_dump_ids": ["abc123...", "def456..."]}

# Step 2: Trigger work with raw_dump sources
curl -X POST http://localhost:8000/api/baskets/123e4567-e89b-12d3-a456-426614174000/work \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "req_12345",
    "basket_id": "123e4567-e89b-12d3-a456-426614174000",
    "sources": [
      {"type": "raw_dump", "id": "abc123..."}
    ],
    "intent": "init_build"
  }'
```

The work route accepts the BasketChangeRequest schema which already supports:
- `sources: List[Source]` where Source can be SourceRawDump
- `SourceRawDump` has fields: `type: "raw_dump"` and `id: str`