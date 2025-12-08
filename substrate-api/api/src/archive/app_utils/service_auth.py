"""
Service authentication utilities for BFF pattern.

Supports both user JWT auth and service-to-service auth.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


def verify_user_or_service(request: Request) -> dict[str, str]:
    """
    Verify request is authenticated via user JWT OR service-to-service auth.

    For BFF pattern: work-platform calls substrate-API with service auth.
    User auth is still checked if the work-platform didn't set service context.

    Returns:
        dict with either:
        - {"user_id": ..., "is_service": False} for user JWT
        - {"service_name": ..., "is_service": True} for service auth
    """
    # Check if service-to-service auth (set by ServiceToServiceAuthMiddleware)
    service_name = getattr(request.state, "service_name", None)
    if service_name:
        logger.debug(f"Service auth: {service_name}")
        return {
            "service_name": service_name,
            "is_service": True,
        }

    # Check for user JWT auth (set by AuthMiddleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return {
            "user_id": str(user_id),
            "is_service": False,
        }

    # No authentication found
    raise HTTPException(status_code=401, detail="Authentication required")


def get_caller_context(auth_info: dict) -> dict:
    """
    Get caller context from auth info for RLS bypass.

    Args:
        auth_info: Result from verify_user_or_service

    Returns:
        Context dict with user_id or service_name
    """
    if auth_info.get("is_service"):
        return {
            "caller_type": "service",
            "service_name": auth_info.get("service_name"),
        }
    else:
        return {
            "caller_type": "user",
            "user_id": auth_info.get("user_id"),
        }
