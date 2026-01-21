# Governed by: /docs/YARNNN_ALERTS_NOTIFICATIONS_CANON.md (v1.0)

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle X-Correlation-Id header for request tracking.
    Generates a new ID if not provided, and echoes it back in the response.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extract or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-Id")
        if not correlation_id:
            correlation_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Store in request state for handler access
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-Id"] = correlation_id
        
        return response