# Governed by: /docs/YARNNN_ALERTS_NOTIFICATIONS_CANON.md (v1.0)

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Any, Optional, List
import uuid

from schemas.base import ApiResponse, ApiError, AcceptedResponse, AppEvent


def ok(
    request: Request,
    data: Any = None,
    notifications: Optional[List[AppEvent]] = None,
    status_code: int = 200
) -> Response:
    """Return a standardized success response with optional notifications."""
    correlation_id = getattr(request.state, "correlation_id", None)
    
    body = ApiResponse(
        ok=True,
        data=data,
        notifications=notifications,
        correlation_id=correlation_id,
    )
    
    return JSONResponse(
        content=body.model_dump(exclude_none=True),
        status_code=status_code,
        headers={"X-Correlation-Id": correlation_id} if correlation_id else None
    )


def error(
    request: Request,
    message: str,
    code: Optional[str] = None,
    status_code: int = 500,
    notifications: Optional[List[AppEvent]] = None
) -> Response:
    """Return a standardized error response."""
    correlation_id = getattr(request.state, "correlation_id", None)
    
    body = ApiError(
        ok=False,
        error={
            "message": message,
            "code": code or "ERROR",
        },
        notifications=notifications,
        correlation_id=correlation_id,
    )
    
    return JSONResponse(
        content=body.model_dump(exclude_none=True),
        status_code=status_code,
        headers={"X-Correlation-Id": correlation_id} if correlation_id else None
    )


def accepted(
    request: Request,
    job_id: str,
    message: str = "Processing started"
) -> Response:
    """Return a 202 Accepted response for async operations."""
    correlation_id = getattr(request.state, "correlation_id", None)
    
    body = AcceptedResponse(
        ok=True,
        accepted=True,
        job_id=job_id,
        message=message,
        correlation_id=correlation_id,
    )
    
    return JSONResponse(
        status_code=202,
        content=body.model_dump(exclude_none=True),
        headers={"X-Correlation-Id": correlation_id} if correlation_id else None
    )