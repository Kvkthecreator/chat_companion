"""
Service Role Authentication for Internal API Calls

Verifies service role tokens for internal system operations that bypass user auth
Used for canon-pure direct operations that don't require user governance
"""

import os
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_service_role(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """
    Verify service role token for internal operations
    
    Canon v2.3: Direct artifact operations use service role for P4 agent calls
    This bypasses user governance for artifact layer operations
    """
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not service_role_key:
        raise HTTPException(
            status_code=500,
            detail="Service role key not configured"
        )
    
    if credentials.credentials != service_role_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid service role credentials"
        )
    
    return True