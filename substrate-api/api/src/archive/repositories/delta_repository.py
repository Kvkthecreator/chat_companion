from typing import List, Optional
from uuid import UUID
import json

class DeltaRepository:
    """Handles all delta-related database operations"""
    
    def __init__(self, db):
        self.db = db
    
    async def persist_delta(self, delta: dict, request_id: str) -> None:
        """Store a delta with its request_id for idempotency"""
        query = """
            INSERT INTO basket_deltas (delta_id, basket_id, payload, created_at)
            VALUES ($1, $2, $3, $4)
        """
        await self.db.execute(
            query,
            values=[
                delta['delta_id'],
                delta['basket_id'],
                json.dumps(delta),
                delta['created_at']
            ]
        )
        
        # Also track for idempotency
        await self.db.execute(
            "INSERT INTO idempotency_keys (request_id, delta_id, created_at) VALUES ($1, $2, NOW())",
            values=[request_id, delta['delta_id']]
        )
    
    async def get_delta(self, delta_id: str) -> Optional[dict]:
        """Retrieve a delta by ID"""
        query = "SELECT payload FROM basket_deltas WHERE delta_id = $1"
        result = await self.db.fetch_one(query, values=[delta_id])
        return json.loads(result['payload']) if result else None
    
    async def list_deltas(self, basket_id: UUID) -> List[dict]:
        """List all deltas for a basket"""
        query = """
            SELECT payload 
            FROM basket_deltas 
            WHERE basket_id = $1 
            ORDER BY created_at DESC
        """
        results = await self.db.fetch_all(query, values=[str(basket_id)])
        return [json.loads(row['payload']) for row in results]
    
    async def apply_delta(self, basket_id: UUID, delta_id: str) -> bool:
        """Mark a delta as applied"""
        query = """
            UPDATE basket_deltas 
            SET applied_at = NOW() 
            WHERE delta_id = $1 AND basket_id = $2
            RETURNING delta_id
        """
        result = await self.db.fetch_one(query, values=[delta_id, str(basket_id)])
        return result is not None