"""Supabase Storage service for reference assets."""

from __future__ import annotations

import logging
import mimetypes
import os
from datetime import datetime, timedelta
from typing import BinaryIO, Optional
from uuid import UUID, uuid4

from ...utils.supabase_client import supabase_admin_client

logger = logging.getLogger(__name__)

STORAGE_BUCKET = "yarnnn-assets"


class StorageService:
    """Service for managing file storage operations."""

    @staticmethod
    def _get_storage_path(basket_id: UUID, asset_id: UUID, filename: str) -> str:
        """Generate storage path for an asset.

        Format: baskets/{basket_id}/assets/{asset_id}/{filename}
        """
        return f"baskets/{basket_id}/assets/{asset_id}/{filename}"

    @staticmethod
    async def upload_file(
        basket_id: UUID,
        filename: str,
        file_content: bytes,
        mime_type: Optional[str] = None,
    ) -> tuple[str, UUID]:
        """Upload file to Supabase Storage.

        Args:
            basket_id: Basket ID for organizing files
            filename: Original filename
            file_content: File content as bytes
            mime_type: MIME type (auto-detected if not provided)

        Returns:
            Tuple of (storage_path, asset_id)

        Raises:
            Exception: If upload fails
        """
        if not supabase_admin_client:
            raise RuntimeError("Supabase admin client not initialized")

        # Generate unique asset ID
        asset_id = uuid4()

        # Get storage path
        storage_path = StorageService._get_storage_path(basket_id, asset_id, filename)

        # Auto-detect MIME type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

        try:
            # Upload to Supabase Storage
            result = supabase_admin_client.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": mime_type,
                    "cache-control": "3600",  # 1 hour
                    "upsert": "false",  # Don't allow overwriting
                },
            )

            logger.info(f"Uploaded file to storage: {storage_path}")
            return storage_path, asset_id

        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise

    @staticmethod
    async def delete_file(storage_path: str) -> bool:
        """Delete file from Supabase Storage.

        Args:
            storage_path: Path to file in storage

        Returns:
            True if deleted successfully, False otherwise
        """
        if not supabase_admin_client:
            raise RuntimeError("Supabase admin client not initialized")

        try:
            result = supabase_admin_client.storage.from_(STORAGE_BUCKET).remove(
                [storage_path]
            )
            logger.info(f"Deleted file from storage: {storage_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file from storage: {e}")
            return False

    @staticmethod
    async def get_signed_url(storage_path: str, expires_in: int = 3600) -> str:
        """Get signed URL for downloading a file.

        Args:
            storage_path: Path to file in storage
            expires_in: URL expiration time in seconds (default: 1 hour)

        Returns:
            Signed URL string

        Raises:
            Exception: If URL generation fails
        """
        if not supabase_admin_client:
            raise RuntimeError("Supabase admin client not initialized")

        try:
            result = supabase_admin_client.storage.from_(STORAGE_BUCKET).create_signed_url(
                path=storage_path,
                expires_in=expires_in,
            )

            if "signedURL" in result:
                return result["signedURL"]
            elif "signedUrl" in result:
                return result["signedUrl"]
            else:
                # Fallback: construct public URL (though bucket is private)
                supabase_url = os.getenv("SUPABASE_URL")
                return f"{supabase_url}/storage/v1/object/sign/{STORAGE_BUCKET}/{storage_path}"

        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise

    @staticmethod
    async def get_file_metadata(storage_path: str) -> Optional[dict]:
        """Get file metadata from storage.

        Args:
            storage_path: Path to file in storage

        Returns:
            File metadata dict or None if not found
        """
        if not supabase_admin_client:
            raise RuntimeError("Supabase admin client not initialized")

        try:
            result = supabase_admin_client.storage.from_(STORAGE_BUCKET).list(
                path=os.path.dirname(storage_path)
            )

            filename = os.path.basename(storage_path)
            for file_info in result:
                if file_info.get("name") == filename:
                    return file_info

            return None

        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            return None
