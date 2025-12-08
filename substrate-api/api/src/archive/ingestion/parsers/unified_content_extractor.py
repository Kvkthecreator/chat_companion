"""Content extraction service for direct file processing (Memory-First approach)."""

from __future__ import annotations

import logging
import tempfile
import os
import mimetypes
from typing import Optional
from urllib.parse import urlparse

from .pdf_text import extract_pdf_text

logger = logging.getLogger("uvicorn.error")

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class ContentExtractor:
    """Service for extracting text content from file bytes (Memory-First approach)."""
    
    @classmethod
    async def extract_content_from_supabase_url(cls, file_url: str, mime_type: Optional[str] = None) -> str:
        """Extract text content from Supabase Storage file URL (Memory-First approach).
        
        Args:
            file_url: Supabase Storage URL for uploaded file
            mime_type: Optional MIME type hint. If not provided, will be inferred.
            
        Returns:
            Extracted text content, or empty string if extraction fails/unsupported
        """
        if not cls._is_supabase_storage_url(file_url):
            logger.warning(f"URL is not a Supabase Storage URL: {file_url}")
            return ""
        
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not available for Supabase file downloading")
            return ""
        
        try:
            # Infer MIME type if not provided
            if not mime_type:
                mime_type = cls._infer_mime_type_from_url(file_url)
            
            if not mime_type:
                logger.warning(f"Could not determine MIME type for {file_url}")
                return ""
            
            # Download file content from Supabase Storage
            file_content = await cls._download_supabase_file(file_url)
            if not file_content:
                return ""
            
            # Process the file bytes (Memory-First)
            return cls.extract_content_from_bytes(file_content, mime_type)
                
        except Exception as e:
            logger.exception(f"Failed to extract content from Supabase URL {file_url}: {e}")
            return ""
    
    @classmethod
    def _is_supabase_storage_url(cls, url: str) -> bool:
        """Check if URL is a Supabase Storage URL."""
        try:
            parsed = urlparse(url)
            # Supabase Storage URLs typically contain 'supabase' and 'storage' in the hostname
            hostname = parsed.hostname or ""
            return 'supabase' in hostname and 'storage' in hostname
        except Exception:
            return False
    
    @classmethod
    def _infer_mime_type_from_url(cls, file_url: str) -> Optional[str]:
        """Infer MIME type from file URL path."""
        try:
            parsed_url = urlparse(file_url)
            path = parsed_url.path
            mime_type, _ = mimetypes.guess_type(path)
            return mime_type
        except Exception:
            return None
    
    @classmethod
    async def _download_supabase_file(cls, file_url: str) -> Optional[bytes]:
        """Download file content from Supabase Storage URL."""
        try:
            async with httpx.AsyncClient(
                timeout=30.0, 
                follow_redirects=True,
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=2)
            ) as client:
                response = await client.get(file_url)
                response.raise_for_status()
                
                # Check content size (max 50MB to prevent memory issues)
                if len(response.content) > 50 * 1024 * 1024:
                    logger.warning(f"File too large ({len(response.content)} bytes): {file_url}")
                    return None
                    
                return response.content
        except Exception as e:
            logger.exception(f"Failed to download Supabase file from {file_url}: {e}")
            return None
    
    @classmethod
    def extract_content_from_bytes(cls, file_content: bytes, mime_type: str) -> str:
        """Extract text content from file bytes based on MIME type.
        
        Args:
            file_content: Raw file bytes
            mime_type: MIME type of the file
            
        Returns:
            Extracted text content, or empty string if extraction fails/unsupported
        """
        if not file_content:
            return ""
        
        try:
            # Route to appropriate extractor based on MIME type
            if mime_type.startswith('image/'):
                return cls._extract_image_text_ocr(file_content)
            elif mime_type == 'application/pdf':
                return cls._extract_pdf_text(file_content)
            elif mime_type.startswith('text/'):
                return cls._extract_text_content(file_content)
            else:
                logger.info(f"Unsupported MIME type for text extraction: {mime_type}")
                return ""
                
        except Exception as e:
            logger.exception(f"Failed to extract content from file bytes: {e}")
            return ""
    
    @classmethod
    def _extract_pdf_text(cls, file_content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            return extract_pdf_text(file_content)
        except Exception as e:
            logger.exception(f"Failed to extract PDF text: {e}")
            return ""
    
    @classmethod
    def _extract_image_text_ocr(cls, file_content: bytes) -> str:
        """Extract text from image using OCR."""
        if not OCR_AVAILABLE:
            logger.warning("OCR dependencies (PIL/pytesseract) not available")
            return ""
        
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file.flush()
                
                try:
                    # Open image and perform OCR
                    with Image.open(temp_file.name) as image:
                        text = pytesseract.image_to_string(image, lang='eng')
                        return text.strip()
                finally:
                    # Clean up temp file
                    os.unlink(temp_file.name)
                    
        except Exception as e:
            logger.exception(f"Failed to extract text from image: {e}")
            return ""
    
    @classmethod
    def _extract_text_content(cls, file_content: bytes) -> str:
        """Extract content from plain text files."""
        try:
            # Try UTF-8 first, fallback to latin-1 for broader compatibility
            try:
                return file_content.decode('utf-8').strip()
            except UnicodeDecodeError:
                return file_content.decode('latin-1', errors='ignore').strip()
        except Exception as e:
            logger.exception(f"Failed to extract text content: {e}")
            return ""
    
    @classmethod
    def get_supported_mime_types(cls) -> list[str]:
        """Get list of canonically supported MIME types for structured content extraction."""
        supported = [
            'application/pdf',
            'text/plain',
            'text/markdown',
        ]
        
        if OCR_AVAILABLE:
            supported.extend([
                'image/jpeg',
                'image/jpg',
                'image/png',
                'image/gif',
                'image/bmp',
                'image/tiff',
                'image/webp'
            ])
        
        return supported
    
    @classmethod
    def is_supported_mime_type(cls, mime_type: str) -> bool:
        """Check if a MIME type is supported for content extraction."""
        return mime_type in cls.get_supported_mime_types()