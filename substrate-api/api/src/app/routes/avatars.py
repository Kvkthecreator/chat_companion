"""Avatar kit and asset management API routes.

Provides endpoints for managing avatar kits (visual identity contracts)
and their associated assets (anchors, expressions, poses).

For MVP, these are admin-only endpoints. Schema supports user-owned kits later.
"""

import logging
import uuid
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from app.deps import get_db
from app.dependencies import get_current_user_id
from app.models.image import (
    AvatarAsset,
    AvatarAssetCreate,
    AvatarAssetWithUrl,
    AvatarKit,
    AvatarKitCreate,
    AvatarKitUpdate,
    AvatarKitWithAnchors,
)
from app.services.storage import StorageService

log = logging.getLogger(__name__)

router = APIRouter(prefix="/avatar-kits", tags=["Avatar Kits"])


# ============================================================================
# Avatar Kit CRUD
# ============================================================================


@router.post("", response_model=AvatarKit, status_code=status.HTTP_201_CREATED)
async def create_avatar_kit(
    data: AvatarKitCreate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Create a new avatar kit for a character.

    The kit starts in 'active' status immediately (simplified governance).
    """
    # Verify character exists
    character = await db.fetch_one(
        "SELECT id, name FROM characters WHERE id = :character_id",
        {"character_id": str(data.character_id)},
    )
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found",
        )

    kit_id = uuid.uuid4()

    query = """
        INSERT INTO avatar_kits (
            id, character_id, created_by, name, description,
            appearance_prompt, style_prompt, negative_prompt,
            status, is_default
        )
        VALUES (
            :id, :character_id, :created_by, :name, :description,
            :appearance_prompt, :style_prompt, :negative_prompt,
            'active', :is_default
        )
        RETURNING *
    """
    row = await db.fetch_one(
        query,
        {
            "id": str(kit_id),
            "character_id": str(data.character_id),
            "created_by": str(user_id),
            "name": data.name,
            "description": data.description,
            "appearance_prompt": data.appearance_prompt,
            "style_prompt": data.style_prompt,
            "negative_prompt": data.negative_prompt,
            "is_default": data.is_default,
        },
    )

    log.info(f"Created avatar kit {kit_id} for character {data.character_id}")
    return AvatarKit(**dict(row))


@router.get("", response_model=List[AvatarKit])
async def list_avatar_kits(
    character_id: Optional[UUID] = Query(None, description="Filter by character"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List avatar kits, optionally filtered by character or status."""
    query = "SELECT * FROM avatar_kits WHERE 1=1"
    params = {}

    if character_id:
        query += " AND character_id = :character_id"
        params["character_id"] = str(character_id)

    if status_filter:
        query += " AND status = :status"
        params["status"] = status_filter

    query += " ORDER BY created_at DESC"

    rows = await db.fetch_all(query, params)
    return [AvatarKit(**dict(row)) for row in rows]


@router.get("/{kit_id}", response_model=AvatarKitWithAnchors)
async def get_avatar_kit(
    kit_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get a specific avatar kit with anchor URLs."""
    query = """
        SELECT ak.*,
               pa.storage_path as primary_anchor_path,
               sa.storage_path as secondary_anchor_path
        FROM avatar_kits ak
        LEFT JOIN avatar_assets pa ON pa.id = ak.primary_anchor_id
        LEFT JOIN avatar_assets sa ON sa.id = ak.secondary_anchor_id
        WHERE ak.id = :kit_id
    """
    row = await db.fetch_one(query, {"kit_id": str(kit_id)})

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar kit not found",
        )

    data = dict(row)
    storage = StorageService.get_instance()

    # Generate signed URLs for anchors
    data["primary_anchor_url"] = None
    data["secondary_anchor_url"] = None

    if data.get("primary_anchor_path"):
        data["primary_anchor_url"] = await storage.create_signed_url(
            "avatars", data["primary_anchor_path"]
        )
    if data.get("secondary_anchor_path"):
        data["secondary_anchor_url"] = await storage.create_signed_url(
            "avatars", data["secondary_anchor_path"]
        )

    # Remove path fields not in model
    data.pop("primary_anchor_path", None)
    data.pop("secondary_anchor_path", None)

    return AvatarKitWithAnchors(**data)


@router.patch("/{kit_id}", response_model=AvatarKit)
async def update_avatar_kit(
    kit_id: UUID,
    data: AvatarKitUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Update an avatar kit's prompts or status."""
    # Build dynamic update query
    updates = []
    params = {"kit_id": str(kit_id)}

    if data.name is not None:
        updates.append("name = :name")
        params["name"] = data.name

    if data.description is not None:
        updates.append("description = :description")
        params["description"] = data.description

    if data.appearance_prompt is not None:
        updates.append("appearance_prompt = :appearance_prompt")
        params["appearance_prompt"] = data.appearance_prompt

    if data.style_prompt is not None:
        updates.append("style_prompt = :style_prompt")
        params["style_prompt"] = data.style_prompt

    if data.negative_prompt is not None:
        updates.append("negative_prompt = :negative_prompt")
        params["negative_prompt"] = data.negative_prompt

    if data.status is not None:
        updates.append("status = :status")
        params["status"] = data.status

    if data.is_default is not None:
        updates.append("is_default = :is_default")
        params["is_default"] = data.is_default

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    updates.append("updated_at = NOW()")
    update_clause = ", ".join(updates)

    query = f"""
        UPDATE avatar_kits
        SET {update_clause}
        WHERE id = :kit_id
        RETURNING *
    """
    row = await db.fetch_one(query, params)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar kit not found",
        )

    return AvatarKit(**dict(row))


@router.delete("/{kit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar_kit(
    kit_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Archive an avatar kit (soft delete via status)."""
    result = await db.execute(
        """
        UPDATE avatar_kits
        SET status = 'archived', updated_at = NOW()
        WHERE id = :kit_id
        """,
        {"kit_id": str(kit_id)},
    )

    # Note: Could check if any rows affected, but 204 is fine either way


# ============================================================================
# Avatar Assets
# ============================================================================


@router.get("/{kit_id}/assets", response_model=List[AvatarAssetWithUrl])
async def list_kit_assets(
    kit_id: UUID,
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List all assets for an avatar kit."""
    # Verify kit exists
    kit = await db.fetch_one(
        "SELECT id FROM avatar_kits WHERE id = :kit_id",
        {"kit_id": str(kit_id)},
    )
    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar kit not found",
        )

    query = """
        SELECT * FROM avatar_assets
        WHERE avatar_kit_id = :kit_id AND is_active = TRUE
    """
    params = {"kit_id": str(kit_id)}

    if asset_type:
        query += " AND asset_type = :asset_type"
        params["asset_type"] = asset_type

    query += " ORDER BY is_canonical DESC, created_at ASC"

    rows = await db.fetch_all(query, params)

    # Generate signed URLs
    storage = StorageService.get_instance()
    results = []
    for row in rows:
        data = dict(row)
        data["image_url"] = await storage.create_signed_url("avatars", data["storage_path"])
        results.append(AvatarAssetWithUrl(**data))

    return results


@router.post("/{kit_id}/assets", response_model=AvatarAssetWithUrl, status_code=status.HTTP_201_CREATED)
async def upload_kit_asset(
    kit_id: UUID,
    file: UploadFile = File(...),
    asset_type: str = Form(..., description="anchor_portrait, anchor_fullbody, expression, pose, outfit"),
    expression: Optional[str] = Form(None, description="Expression name for expression assets"),
    emotion_tags: Optional[str] = Form(None, description="Comma-separated emotion tags"),
    is_canonical: bool = Form(False, description="Whether this is a canonical/anchor asset"),
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Upload an asset to an avatar kit.

    Supported asset types:
    - anchor_portrait: Primary face reference (shoulders up)
    - anchor_fullbody: Full body reference
    - expression: Expression variant (e.g., happy, shy)
    - pose: Pose variant
    - outfit: Outfit variant
    """
    # Validate asset type
    valid_types = ["anchor_portrait", "anchor_fullbody", "expression", "pose", "outfit"]
    if asset_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset_type. Must be one of: {valid_types}",
        )

    # Verify kit exists
    kit = await db.fetch_one(
        "SELECT id FROM avatar_kits WHERE id = :kit_id",
        {"kit_id": str(kit_id)},
    )
    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar kit not found",
        )

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Read file content
    image_bytes = await file.read()
    asset_id = uuid.uuid4()

    # Upload to storage
    storage = StorageService.get_instance()
    storage_path = await storage.upload_avatar_asset(
        image_bytes=image_bytes,
        kit_id=kit_id,
        asset_id=asset_id,
        asset_type=asset_type,
    )

    # Parse emotion tags
    tags = []
    if emotion_tags:
        tags = [t.strip() for t in emotion_tags.split(",") if t.strip()]

    # Anchors are canonical by default
    if asset_type in ["anchor_portrait", "anchor_fullbody"]:
        is_canonical = True

    # Save to database
    query = """
        INSERT INTO avatar_assets (
            id, avatar_kit_id, asset_type, expression, emotion_tags,
            storage_bucket, storage_path, source_type, is_canonical,
            mime_type, file_size_bytes
        )
        VALUES (
            :id, :kit_id, :asset_type, :expression, :emotion_tags,
            'avatars', :storage_path, 'manual_upload', :is_canonical,
            :mime_type, :file_size_bytes
        )
        RETURNING *
    """
    row = await db.fetch_one(
        query,
        {
            "id": str(asset_id),
            "kit_id": str(kit_id),
            "asset_type": asset_type,
            "expression": expression,
            "emotion_tags": tags,
            "storage_path": storage_path,
            "is_canonical": is_canonical,
            "mime_type": file.content_type,
            "file_size_bytes": len(image_bytes),
        },
    )

    log.info(f"Uploaded avatar asset {asset_id} to kit {kit_id}: {asset_type}")

    # Generate signed URL for response
    data = dict(row)
    data["image_url"] = await storage.create_signed_url("avatars", storage_path)

    return AvatarAssetWithUrl(**data)


@router.delete("/{kit_id}/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kit_asset(
    kit_id: UUID,
    asset_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Soft-delete an avatar asset."""
    result = await db.execute(
        """
        UPDATE avatar_assets
        SET is_active = FALSE
        WHERE id = :asset_id AND avatar_kit_id = :kit_id
        """,
        {"asset_id": str(asset_id), "kit_id": str(kit_id)},
    )


# ============================================================================
# Anchor Management
# ============================================================================


@router.patch("/{kit_id}/primary-anchor", response_model=AvatarKit)
async def set_primary_anchor(
    kit_id: UUID,
    asset_id: UUID = Query(..., description="Asset ID to set as primary anchor"),
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Set the primary anchor for an avatar kit."""
    # Verify asset exists and belongs to kit
    asset = await db.fetch_one(
        """
        SELECT id, asset_type FROM avatar_assets
        WHERE id = :asset_id AND avatar_kit_id = :kit_id AND is_active = TRUE
        """,
        {"asset_id": str(asset_id), "kit_id": str(kit_id)},
    )

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found in this kit",
        )

    # Update kit
    row = await db.fetch_one(
        """
        UPDATE avatar_kits
        SET primary_anchor_id = :asset_id, updated_at = NOW()
        WHERE id = :kit_id
        RETURNING *
        """,
        {"asset_id": str(asset_id), "kit_id": str(kit_id)},
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar kit not found",
        )

    # Mark asset as canonical
    await db.execute(
        "UPDATE avatar_assets SET is_canonical = TRUE WHERE id = :asset_id",
        {"asset_id": str(asset_id)},
    )

    return AvatarKit(**dict(row))


@router.patch("/{kit_id}/secondary-anchor", response_model=AvatarKit)
async def set_secondary_anchor(
    kit_id: UUID,
    asset_id: UUID = Query(..., description="Asset ID to set as secondary anchor"),
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Set the secondary anchor for an avatar kit."""
    # Verify asset exists and belongs to kit
    asset = await db.fetch_one(
        """
        SELECT id, asset_type FROM avatar_assets
        WHERE id = :asset_id AND avatar_kit_id = :kit_id AND is_active = TRUE
        """,
        {"asset_id": str(asset_id), "kit_id": str(kit_id)},
    )

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found in this kit",
        )

    # Update kit
    row = await db.fetch_one(
        """
        UPDATE avatar_kits
        SET secondary_anchor_id = :asset_id, updated_at = NOW()
        WHERE id = :kit_id
        RETURNING *
        """,
        {"asset_id": str(asset_id), "kit_id": str(kit_id)},
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar kit not found",
        )

    # Mark asset as canonical
    await db.execute(
        "UPDATE avatar_assets SET is_canonical = TRUE WHERE id = :asset_id",
        {"asset_id": str(asset_id)},
    )

    return AvatarKit(**dict(row))


# ============================================================================
# Character-Kit Association
# ============================================================================


@router.get("/character/{character_id}", response_model=List[AvatarKit])
async def list_character_kits(
    character_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """List all avatar kits for a character."""
    rows = await db.fetch_all(
        """
        SELECT * FROM avatar_kits
        WHERE character_id = :character_id AND status != 'archived'
        ORDER BY is_default DESC, created_at DESC
        """,
        {"character_id": str(character_id)},
    )
    return [AvatarKit(**dict(row)) for row in rows]


@router.patch("/character/{character_id}/active-kit", response_model=dict)
async def set_active_kit(
    character_id: UUID,
    kit_id: UUID = Query(..., description="Kit ID to set as active"),
    user_id: UUID = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Set the active avatar kit for a character."""
    # Verify kit exists and belongs to character
    kit = await db.fetch_one(
        """
        SELECT id, name, status FROM avatar_kits
        WHERE id = :kit_id AND character_id = :character_id
        """,
        {"kit_id": str(kit_id), "character_id": str(character_id)},
    )

    if not kit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kit not found for this character",
        )

    if kit["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Kit must be in 'active' status to be set as active kit",
        )

    # Update character
    await db.execute(
        """
        UPDATE characters
        SET active_avatar_kit_id = :kit_id
        WHERE id = :character_id
        """,
        {"kit_id": str(kit_id), "character_id": str(character_id)},
    )

    log.info(f"Set active kit {kit_id} for character {character_id}")

    return {
        "character_id": str(character_id),
        "active_kit_id": str(kit_id),
        "kit_name": kit["name"],
    }
