from typing import List, Optional
from uuid import UUID
import json
from datetime import datetime

class BasketRepository:
    """Handles all basket-related database operations"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_basket(self, basket_id: UUID) -> Optional[dict]:
        """Retrieve a basket by ID"""
        query = "SELECT * FROM baskets WHERE id = $1"
        result = await self.db.fetch_one(query, values=[str(basket_id)])
        return dict(result) if result else None
    
    async def create_basket(self, basket_data: dict) -> dict:
        """Create a new basket"""
        query = """
            INSERT INTO baskets (id, name, status, workspace_id, mode, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        result = await self.db.fetch_one(
            query,
            values=[
                basket_data.get('id'),
                basket_data.get('name'),
                basket_data.get('status', 'ACTIVE'),
                basket_data.get('workspace_id'),
                basket_data.get('mode', 'default'),
                datetime.utcnow()
            ]
        )
        return dict(result)
    
    async def update_basket(self, basket_id: UUID, updates: dict) -> Optional[dict]:
        """Update a basket"""
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(updates.keys())])
        query = f"""
            UPDATE baskets 
            SET {set_clause}, updated_at = NOW()
            WHERE id = $1
            RETURNING *
        """
        values = [str(basket_id)] + list(updates.values())
        result = await self.db.fetch_one(query, values=values)
        return dict(result) if result else None
