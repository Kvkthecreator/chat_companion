# Canon v2.0 — Substrate/Artifact Model

# YARNNN Ingestion Canon (Authoritative)

## Core Ingestion Paths

### 1. Traditional Capture Path (Preserved)
Default path: POST /api/baskets/new then fan-out POST /api/dumps/new.
Optional path: POST /api/baskets/ingest reduces round-trips during onboarding (idempotent on basket & each dump).

### 2. Document Upload Path (New in v1.4.0)
**Entry Point**: `/baskets/[id]/memory` page → Upload Document button → Modal
**Flow**: File Upload → Document Creation → raw_dump Linkage → Agent Processing
- Creates `document` record via `POST /api/documents` → calls `fn_document_create`
- Links files or supporting text to `raw_dumps` via `POST /api/dumps/upload` (supports `files[]` + optional `text_dump` in a single request)
- Agent processes raw_dump asynchronously → creates blocks via governance
- User can optionally compose resulting blocks into document narrative

**API Schema**: Document creation requires `{basket_id, title, metadata?}` (NOT substrate_type)
**File Processing**: Uses `/api/dumps/upload` with canonical formats (text, PDF, images); each request may include multiple files and shared metadata.

Blocks (substrate_type: 'block' in context_blocks table) are structured knowledge ingredients extracted from dumps (substrate_type: 'dump' in raw_dumps table). Reflections are artifacts, not substrates.

## Contract
- **Single dump**: `POST /api/dumps/new`
  - Body: `{ basket_id, dump_request_id, text_dump?, file_url?, meta? }`
  - Writes `raw_dumps`. **DB trigger** emits `timeline_events(kind='dump')`.
  - **Idempotency**: `(basket_id, dump_request_id)` unique; replay returns the same dump_id.

- **Batch ingest**: `POST /api/baskets/ingest` → RPC `fn_ingest_dumps(p_workspace_id, p_basket_id, p_dumps jsonb)`

**Optional onboarding alias:** **POST /api/baskets/ingest** orchestrates basket + multiple dumps in one transaction; it performs **no additional side-effects** beyond the split endpoints and is idempotent on both the basket and each dump.

## Flow (Governance-First Evolution)

**Sacred Capture Path** (Preserved):
Capture → `/api/dumps/new` → `fn_ingest_dumps` → `raw_dumps`
→ trigger `fn_timeline_after_raw_dump` → `timeline_events('dump')`

**Governance Integration** (New):
→ P1 Substrate Agent extracts structured knowledge (goals, constraints, metrics, entities) → creates proposals via `fn_proposal_create`
→ governance review → `fn_proposal_approve` → commits substrate operations
→ each approval inserts blocks and context items directly through service-role clients (`blocks`, `context_items`), respecting substrate equality.

**Manual Substrate Path** (New):
User intent → agent validation → `fn_proposal_create` → governance → substrate commitment

## Idempotency & Trace
- Client generates `dump_request_id` (UUID).
- Unique index: `(basket_id, dump_request_id) WHERE dump_request_id IS NOT NULL`.
- Trace/context fields may be nested under `meta`; server may record additional trace internally.

Clients may include additional trace/context fields inside `meta` (e.g., `meta.client_trace_id`); the server may also record a server-generated trace internally. These are not part of the public DTO surface.

## Security
- All writes scoped by `workspace_id`; RLS enforces workspace membership.  
- Functions have `GRANT EXECUTE TO authenticated`.

## Error Model
- 401/403 auth; 422 validation; 409 idempotency conflict; 500 unexpected.

## RPCs
- `fn_ingest_dumps`, `fn_reflection_cache_upsert` (optional), `fn_document_create`, `fn_block_create`,
  `fn_block_revision_create`, `fn_relationship_upsert_bulk`.

## Tests
- Replaying the same `dump_request_id` returns the same `dump_id` and **exactly one** timeline `dump`.


# Memory-First Content Processing Architecture

## Overview

The content processing system follows a strict **Memory-First philosophy** for uploaded files while treating user-pasted URLs simply as text content. This ensures alignment with YARNNN canon principles of immutable raw dumps and backend-only processing.

## Core Philosophy: Memory-First

- **Supabase Storage file processing**: Uploaded files stored in Supabase Storage are downloaded and processed as bytes
- **Text content only**: All user input is treated as text content - no special URL processing or collection
- **Immutable raw_dumps**: Content extraction creates stable text representation
- **Reliable substrate**: Supabase Storage ensures file availability for processing

## Architecture Components

### Backend: File Processing Only
- **ContentExtractor** (`/api/src/app/ingestion/parsers/unified_content_extractor.py`): 
  - Processes Supabase Storage files by downloading and extracting content from bytes
  - Direct byte processing for immediate file content extraction
- **DumpInterpreterService** (`/api/src/app/agents/services/dump_interpreter.py`): 
  - Processes text content from `body_md` (all user text input)
  - Processes Supabase Storage files via `file_url` field
- **Strategy**: 
  - **All user text**: Stored as text in `body_md`, no special URL handling
  - **Uploaded Files**: Stored in Supabase Storage, downloaded and content extracted during interpretation

### Frontend: Simplified Input
- **No URL collection**: Removed URL input fields and special URL handling
- **Text + Files only**: Users can input text and upload files
- **All text as-is**: URLs pasted as text are just treated as text content

## Supported File Types (Canonical v2.0 - Supabase Storage Only)

### Canon-Compliant Formats (Memory-First Processing)
- **Text files** (`.txt`, `.md`): Direct content reading from downloaded bytes - immediate text processing
- **PDF files** (`.pdf`): Structured text extraction via PyMuPDF from downloaded bytes - intelligent parsing
- **Images** (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.webp`): OCR text extraction via Tesseract from downloaded bytes - visual content processing

### Removed Legacy Formats (Canon Consolidation)
- ❌ **CSV files** (`.csv`): Removed - tail data format with poor structured extraction
- ❌ **HTML files** (`.html`): Removed - tail data format with poor structured extraction  
- ❌ **Office documents** (`.doc`, `.docx`): Never supported - not in canonical format set

### Canon Philosophy: Structured Content Extraction
- **Text formats**: Immediate text content processing for direct substrate creation
- **Binary formats**: Supabase Storage + structured extraction (PDF parsing, OCR) for knowledge ingredient extraction
- **Batch processing**: Multiple files processed together for unified substrate analysis via P1 Substrate Agent
- **No tail formats**: Focus on formats with proven structured knowledge extraction capabilities

### Extension Points (Canon-Compliant)
- Additional canonical file types can be added to `ContentExtractor.get_supported_mime_types()`
- New parsers must follow: `supabase_url → download_bytes → structured_text_extraction → knowledge_ingredients`
- All new formats must support LLM-based structured knowledge extraction (goals, constraints, metrics, entities)

## Memory-First Benefits

### Canon Compliance
✅ **Backend-only processing**: All extraction happens server-side from memory  
✅ **Immutable raw_dumps**: Content stored as text, no external dependencies  
✅ **Agent-driven**: Uses existing DumpInterpreterService for text processing  
✅ **Reliable substrate**: No broken links or unavailable files  

### Reliability
- **No network dependencies**: Processing works offline
- **Consistent results**: Same file bytes always produce same text
- **Fast processing**: No download latency or timeouts
- **Secure**: Files processed in controlled server environment

## Implementation Details

### Supabase Storage File Processing
```python
from api.src.app.ingestion.parsers import ContentExtractor

# Two approaches:

# 1. Direct bytes processing (immediate upload processing)
file_content = request.files['upload'].read()  # bytes
mime_type = request.files['upload'].content_type
extracted_text = ContentExtractor.extract_content_from_bytes(file_content, mime_type)

# 2. Supabase Storage URL processing (during interpretation)
supabase_file_url = "https://abc.supabase.co/storage/v1/object/public/uploads/doc.pdf"
extracted_text = await ContentExtractor.extract_content_from_supabase_url(supabase_file_url, mime_type)

# Store extracted text in raw_dump
raw_dump.body_md = extracted_text  # Direct processing
# OR
raw_dump.file_url = supabase_file_url  # Process during interpretation
```

### Error Handling
- **Graceful degradation**: Unsupported file types return empty string
- **Memory management**: Large files handled efficiently with temp files for images
- **Type validation**: MIME type checking prevents processing of unsupported formats

## Configuration

### Required Dependencies (Canonical v2.0)
```python
# Core file processing (Memory-First, Canon-Compliant)
pymupdf>=1.24.0        # PDF structured text extraction from bytes
httpx>=0.25.0          # Supabase Storage file downloading for canonical processing

# Canonical OCR for image bytes (structured text extraction)
Pillow>=10.0.0         # Image processing from bytes for OCR pipeline
pytesseract>=0.3.10    # OCR engine (requires tesseract system package)

# Canon-compliant constants
# shared/constants/canonical_file_types.ts - Authoritative format definitions
```

### Environment Setup
```bash
# For OCR support (optional)
sudo apt-get install tesseract-ocr  # Ubuntu/Debian
brew install tesseract              # macOS
```

## Testing Memory-First Processing

### Unit Test Example
```python
# Test direct byte processing
pdf_bytes = open('test.pdf', 'rb').read()
extracted_text = ContentExtractor.extract_content_from_bytes(pdf_bytes, 'application/pdf')
assert extracted_text.strip() != ""

# Test MIME type support
supported_types = ContentExtractor.get_supported_mime_types()
assert 'application/pdf' in supported_types
```

### Integration Points
- **Upload handlers**: Store uploaded files in Supabase Storage as `file_url`
- **Raw dump creation**: Store user text as `body_md` AND/OR Supabase Storage URL as `file_url`
- **Agent interpretation**: Process text content from `body_md` AND extract content from `file_url` if present
- **Text input**: All user text (including URLs) stored as text in `body_md`, no special processing

## Future Enhancements

### Planned Memory-First Extensions
- **Structured extraction**: Preserve formatting and structure from file bytes
- **Metadata extraction**: Extract file properties (author, creation date, etc.)
- **Multi-format support**: Add support for Office documents, archives, etc.
- **Content validation**: Verify extracted content quality and completeness

### Performance Optimizations
- **Streaming processing**: Handle large files without loading entirely into memory
- **Parallel processing**: Process multiple files concurrently
- **Caching**: Cache extraction results for identical file bytes
- **Background processing**: Queue large file processing for async handling

## Troubleshooting

### Common Issues
- **Missing OCR dependencies**: Pillow/pytesseract optional, graceful degradation
- **Large file handling**: Temporary files used for image processing, cleaned up automatically  
- **Unsupported formats**: Logged but don't cause processing failures
- **Memory usage**: File bytes processed efficiently, not stored long-term

### Debug Commands
```python
# Test file processing
from api.src.app.ingestion.parsers import ContentExtractor

# Check supported MIME types
supported = ContentExtractor.get_supported_mime_types()
print(f"Supported types: {supported}")

# Test direct file byte processing
with open('test.pdf', 'rb') as f:
    content = ContentExtractor.extract_content_from_bytes(f.read(), 'application/pdf')
    print(f"Direct processing extracted: {len(content)} characters")

# Test Supabase Storage URL processing
supabase_url = "https://abc.supabase.co/storage/v1/object/public/uploads/test.pdf"
content = await ContentExtractor.extract_content_from_supabase_url(supabase_url, 'application/pdf')
print(f"Supabase URL processing extracted: {len(content)} characters")

# Check if URL is Supabase Storage
is_supabase = ContentExtractor._is_supabase_storage_url(supabase_url)
print(f"Is Supabase Storage URL: {is_supabase}")
```

## Memory-First vs URL-Based Comparison

| Aspect | Memory-First ✅ | URL-Based ❌ |
|--------|----------------|-------------|
| **Reliability** | Always available | Links can break |
| **Security** | Server-controlled | External dependencies |
| **Performance** | No network calls | Download latency |
| **Canon Compliance** | Immutable substrate | External references |
| **Offline Support** | Works offline | Requires connectivity |
| **Consistency** | Same input = same output | URLs can change |

The Memory-First approach ensures robust, reliable content processing that aligns perfectly with YARNNN's philosophy of creating an immutable, self-contained intelligence substrate.
