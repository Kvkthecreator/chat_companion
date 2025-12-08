"""
P0 Capture Agent - YARNNN Canon v1.4.0 Compliant

Sacred Rule: Only writes raw_dumps, never interprets content
Pipeline: P0_CAPTURE

This agent handles dump ingestion requests and persists raw memory
without any interpretation or analysis.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
from pydantic import BaseModel

from infra.utils.supabase_client import supabase_admin_client as supabase
from app.ingestion.parsers.unified_content_extractor import ContentExtractor

logger = logging.getLogger("uvicorn.error")


class DumpIngestionRequest(BaseModel):
    """Request to ingest raw dump content."""
    basket_id: UUID
    workspace_id: UUID  
    text_dump: Optional[str] = None
    file_url: Optional[str] = None
    source_meta: Optional[Dict[str, Any]] = None
    dump_request_id: UUID


class DumpResult(BaseModel):
    """Result of dump ingestion."""
    dump_id: UUID
    processing_time_ms: int
    content_length: int
    has_file_content: bool


class P0CaptureAgent:
    """
    Canonical P0 Capture pipeline agent.
    
    Sacred Rule: Only writes raw_dumps, never interprets content.
    This agent is responsible for pure capture operations only.
    """
    
    pipeline = "P0_CAPTURE"
    agent_name = "P0CaptureAgent"
    
    def __init__(self):
        self.logger = logger
        
    async def process_dump_ingestion(self, request: DumpIngestionRequest) -> DumpResult:
        """
        Process dump ingestion request with no interpretation.
        
        Operations allowed:
        - File content extraction from Supabase Storage
        - Text normalization and validation  
        - Metadata capture
        - Dump persistence via fn_ingest_dumps RPC
        
        Operations forbidden:
        - Content interpretation
        - Block creation
        - Analysis or processing
        - Any intelligence operations
        """
        start_time = datetime.utcnow()
        
        try:
            # Extract file content if URL provided (P0 operation)
            file_content = None
            if request.file_url:
                file_content = await self._extract_file_content(request.file_url)
                
            # Combine text and file content (P0 operation)
            combined_content = self._combine_content_sources(
                text_dump=request.text_dump,
                file_content=file_content
            )
            
            # Validate and normalize content (P0 operation)  
            normalized_content = self._normalize_content(combined_content)
            
            # Prepare dump data for persistence (P0 operation)
            dump_data = {
                "dump_request_id": str(request.dump_request_id),
                "text_dump": normalized_content if normalized_content else None,
                "file_url": request.file_url if request.file_url else None, 
                "source_meta": request.source_meta if request.source_meta else None,
                "ingest_trace_id": request.source_meta.get("ingest_trace_id") if request.source_meta else None
            }
            
            # Persist dump via RPC (P0 operation)
            response = supabase.rpc("fn_ingest_dumps", {
                "p_workspace_id": str(request.workspace_id),
                "p_basket_id": str(request.basket_id), 
                "p_dumps": [dump_data]
            }).execute()
            
            if response.data and len(response.data) > 0:
                dump_id = UUID(response.data[0]["dump_id"])
            else:
                raise RuntimeError("Dump ingestion RPC returned no dump_id")
                
            # Calculate metrics
            processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            content_length = len(normalized_content) if normalized_content else 0
            
            self.logger.info(
                f"P0 Capture completed: dump_id={dump_id}, "
                f"content_length={content_length}, "
                f"processing_time_ms={processing_time_ms}"
            )
            
            return DumpResult(
                dump_id=dump_id,
                processing_time_ms=processing_time_ms,
                content_length=content_length,
                has_file_content=bool(file_content)
            )
            
        except Exception as e:
            self.logger.error(f"P0 Capture failed for basket {request.basket_id}: {e}")
            raise
    
    async def _extract_file_content(self, file_url: str) -> Optional[str]:
        """
        Extract content from Supabase Storage file.
        This is a P0 operation - pure extraction without interpretation.
        """
        try:
            # Use structured content extraction for canonical file types
            content = await ContentExtractor.extract_content_from_supabase_url(file_url)
            
            if content and content.strip():
                self.logger.info(f"P0 extracted {len(content)} chars from file: {file_url}")
                return content.strip()
            else:
                self.logger.warning(f"P0 file extraction returned empty content: {file_url}")
                return None
                
        except Exception as e:
            self.logger.warning(f"P0 file extraction failed for {file_url}: {e}")
            return None
    
    def _combine_content_sources(
        self, 
        text_dump: Optional[str], 
        file_content: Optional[str]
    ) -> Optional[str]:
        """
        Combine text and file content sources.
        This is a P0 operation - simple concatenation without interpretation.
        """
        parts = []
        
        if text_dump and text_dump.strip():
            parts.append(text_dump.strip())
            
        if file_content and file_content.strip():
            parts.append(file_content.strip())
            
        return "\n\n".join(parts) if parts else None
    
    def _normalize_content(self, content: Optional[str]) -> Optional[str]:
        """
        Normalize content for storage.
        This is a P0 operation - basic cleanup without interpretation.
        """
        if not content:
            return None
            
        # Basic normalization: strip whitespace, ensure minimum length
        normalized = content.strip()
        
        if len(normalized) < 1:
            return None
            
        return normalized
    
    def get_agent_info(self) -> Dict[str, str]:
        """Get agent information."""
        return {
            "name": self.agent_name,
            "pipeline": self.pipeline,
            "type": "capture",
            "status": "active",
            "sacred_rule": "Only writes raw_dumps, never interprets"
        }