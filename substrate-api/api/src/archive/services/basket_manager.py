"""Basket Manager Service - Example of proper database usage with the Manager Agent pattern."""

from __future__ import annotations

import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..deps import get_db, db_transaction
from ..utils.db import json_safe

logger = logging.getLogger("uvicorn.error")


class BasketManagerService:
    """
# V3.0 DEPRECATION NOTICE:
# This file contains references to context_items table which was merged into blocks table.
# Entity blocks are now identified by semantic_type='entity'.
# This file is legacy/supporting code - update if actively maintained.

    Manager Agent Service for basket operations.
    
    This service demonstrates the proper database usage pattern with:
    - Idempotent database connections
    - Transaction support
    - Error handling
    - Proper async operations
    """
    
    @classmethod
    async def create_basket(
        cls,
        workspace_id: str,
        name: str,
        description: Optional[str] = None,
        status: str = "active",
        metadata: Optional[Dict[str, Any]] = None,
        mode: str = "default",
    ) -> Dict[str, Any]:
        """Create a new basket with proper transaction handling."""
        
        basket_id = str(uuid.uuid4())
        
        try:
            async with db_transaction() as db:
                # Insert basket
                basket_data = {
                    "id": basket_id,
                    "workspace_id": workspace_id,
                    "name": name,
                    "description": description,
                    "status": status,
                    "metadata": metadata or {},
                    "mode": mode,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }

                insert_query = """
                    INSERT INTO baskets (id, workspace_id, name, description, status, metadata, mode, created_at, updated_at)
                    VALUES (:id, :workspace_id, :name, :description, :status, :metadata, :mode, :created_at, :updated_at)
                    RETURNING *
                """
                
                result = await db.fetch_one(insert_query, basket_data)
                
                # Log the creation event
                event_data = {
                    "id": str(uuid.uuid4()),
                    "basket_id": basket_id,
                    "workspace_id": workspace_id,
                    "kind": "basket_created",
                    "payload": json_safe({
                        "basket_name": name,
                        "created_by": "manager_agent",
                        "timestamp": datetime.utcnow()
                    }),
                    "ts": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
                
                event_query = """
                    INSERT INTO events (id, basket_id, workspace_id, kind, payload, ts, created_at)
                    VALUES (:id, :basket_id, :workspace_id, :kind, :payload, :ts, :created_at)
                """
                
                await db.execute(event_query, event_data)
                
                logger.info(f"Created basket {basket_id} in workspace {workspace_id}")
                
                return dict(result)
                
        except Exception as e:
            logger.exception(f"Failed to create basket: {e}")
            raise
    
    @classmethod
    async def get_basket(
        cls,
        basket_id: str,
        workspace_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a basket with proper error handling."""
        
        try:
            db = await get_db()
            
            query = """
                SELECT * FROM baskets 
                WHERE id = :basket_id AND workspace_id = :workspace_id
            """
            
            result = await db.fetch_one(query, {
                "basket_id": basket_id,
                "workspace_id": workspace_id
            })
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.exception(f"Failed to get basket {basket_id}: {e}")
            raise
    
    @classmethod
    async def update_basket(
        cls,
        basket_id: str,
        workspace_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update a basket with transaction support."""
        
        try:
            async with db_transaction() as db:
                # Build dynamic update query
                update_fields = []
                params = {
                    "basket_id": basket_id,
                    "workspace_id": workspace_id,
                    "updated_at": datetime.utcnow()
                }
                
                for key, value in updates.items():
                    if key not in ["id", "workspace_id", "created_at"]:  # Protect immutable fields
                        update_fields.append(f"{key} = :{key}")
                        params[key] = value
                
                if not update_fields:
                    raise ValueError("No valid fields to update")
                
                query = f"""
                    UPDATE baskets 
                    SET {', '.join(update_fields)}, updated_at = :updated_at
                    WHERE id = :basket_id AND workspace_id = :workspace_id
                    RETURNING *
                """
                
                result = await db.fetch_one(query, params)
                
                if not result:
                    raise ValueError(f"Basket {basket_id} not found or access denied")
                
                # Log the update event
                event_data = {
                    "id": str(uuid.uuid4()),
                    "basket_id": basket_id,
                    "workspace_id": workspace_id,
                    "kind": "basket_updated",
                    "payload": json_safe({
                        "updates": updates,
                        "updated_by": "manager_agent",
                        "timestamp": datetime.utcnow()
                    }),
                    "ts": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
                
                event_query = """
                    INSERT INTO events (id, basket_id, workspace_id, kind, payload, ts, created_at)
                    VALUES (:id, :basket_id, :workspace_id, :kind, :payload, :ts, :created_at)
                """
                
                await db.execute(event_query, event_data)
                
                logger.info(f"Updated basket {basket_id} with {len(updates)} changes")
                
                return dict(result)
                
        except Exception as e:
            logger.exception(f"Failed to update basket {basket_id}: {e}")
            raise
    
    @classmethod
    async def list_baskets(
        cls,
        workspace_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List baskets with pagination and filtering."""
        
        try:
            db = await get_db()
            
            params = {
                "workspace_id": workspace_id,
                "limit": limit,
                "offset": offset
            }
            
            where_clause = "WHERE workspace_id = :workspace_id"
            if status:
                where_clause += " AND status = :status"
                params["status"] = status
            
            query = f"""
                SELECT * FROM baskets 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            results = await db.fetch_all(query, params)
            
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.exception(f"Failed to list baskets for workspace {workspace_id}: {e}")
            raise
    
    @classmethod
    async def delete_basket(
        cls,
        basket_id: str,
        workspace_id: str
    ) -> bool:
        """Delete a basket with proper cleanup."""
        
        try:
            async with db_transaction() as db:
                # Check if basket exists
                check_query = """
                    SELECT id FROM baskets 
                    WHERE id = :basket_id AND workspace_id = :workspace_id
                """
                
                existing = await db.fetch_one(check_query, {
                    "basket_id": basket_id,
                    "workspace_id": workspace_id
                })
                
                if not existing:
                    return False
                
                # Log deletion event first
                event_data = {
                    "id": str(uuid.uuid4()),
                    "basket_id": basket_id,
                    "workspace_id": workspace_id,
                    "kind": "basket_deleted",
                    "payload": json_safe({
                        "deleted_by": "manager_agent",
                        "timestamp": datetime.utcnow()
                    }),
                    "ts": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
                
                event_query = """
                    INSERT INTO events (id, basket_id, workspace_id, kind, payload, ts, created_at)
                    VALUES (:id, :basket_id, :workspace_id, :kind, :payload, :ts, :created_at)
                """
                
                await db.execute(event_query, event_data)
                
                # Delete the basket (cascades will handle related data)
                delete_query = """
                    DELETE FROM baskets 
                    WHERE id = :basket_id AND workspace_id = :workspace_id
                """
                
                await db.execute(delete_query, {
                    "basket_id": basket_id,
                    "workspace_id": workspace_id
                })
                
                logger.info(f"Deleted basket {basket_id} from workspace {workspace_id}")
                
                return True
                
        except Exception as e:
            logger.exception(f"Failed to delete basket {basket_id}: {e}")
            raise
    
    @classmethod
    async def get_basket_stats(
        cls,
        basket_id: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive stats for a basket."""
        
        try:
            db = await get_db()
            
            # Get counts for all related entities
            stats_query = """
                SELECT 
                    (SELECT COUNT(*) FROM documents WHERE basket_id = :basket_id AND workspace_id = :workspace_id) as document_count,
                    (SELECT COUNT(*) FROM blocks WHERE basket_id = :basket_id AND workspace_id = :workspace_id AND state != 'REJECTED') as block_count,
                    (SELECT COUNT(*) FROM context_items WHERE basket_id = :basket_id AND status = 'active') as context_count,
                    (SELECT COUNT(*) FROM raw_dumps WHERE basket_id = :basket_id AND workspace_id = :workspace_id) as dump_count,
                    (SELECT COUNT(*) FROM events WHERE basket_id = :basket_id AND workspace_id = :workspace_id) as event_count
            """
            
            result = await db.fetch_one(stats_query, {
                "basket_id": basket_id,
                "workspace_id": workspace_id
            })
            
            return dict(result) if result else {}
            
        except Exception as e:
            logger.exception(f"Failed to get stats for basket {basket_id}: {e}")
            raise
    
    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """Health check for the database connection."""
        
        try:
            db = await get_db()
            
            # Simple query to test connection
            result = await db.fetch_one("SELECT NOW() as current_time")
            
            return {
                "status": "healthy",
                "database_connected": True,
                "current_time": result["current_time"] if result else None
            }
            
        except Exception as e:
            logger.exception("Database health check failed")
            return {
                "status": "unhealthy",
                "database_connected": False,
                "error": str(e)
            }
