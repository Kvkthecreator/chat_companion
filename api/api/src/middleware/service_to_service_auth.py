"""
Service-to-service authentication middleware for Substrate API.

Phase 3.1: BFF Foundation - Validates requests from Platform API and other services.

This is separate from service_auth.py which handles service role operations.
This middleware handles inter-service HTTP authentication for BFF architecture.

Security Model:
- Shared secret authentication via Bearer token
- Rate limiting per service
- Request logging for audit trail
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("uvicorn.error")


class ServiceRateLimiter:
    """
    Simple in-memory rate limiter for service-to-service requests.

    Production: Replace with Redis-based rate limiter for distributed deployments.
    """

    def __init__(self, requests_per_minute: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        # service_name -> list of (timestamp, request_count)
        self.request_log: dict[str, list[tuple[float, int]]] = defaultdict(list)

    def check_rate_limit(self, service_name: str) -> tuple[bool, Optional[int]]:
        """
        Check if service is within rate limit.

        Args:
            service_name: Name of the calling service

        Returns:
            (allowed, retry_after_seconds)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        if service_name in self.request_log:
            self.request_log[service_name] = [
                (ts, count)
                for ts, count in self.request_log[service_name]
                if ts >= window_start
            ]

        # Count requests in current window
        request_count = sum(
            count for _, count in self.request_log.get(service_name, [])
        )

        if request_count >= self.requests_per_minute:
            # Calculate retry_after based on oldest request in window
            if self.request_log[service_name]:
                oldest_ts = min(ts for ts, _ in self.request_log[service_name])
                retry_after = int(oldest_ts + self.window_seconds - now) + 1
                return False, retry_after
            return False, self.window_seconds

        # Record this request
        self.request_log[service_name].append((now, 1))
        return True, None

    def reset_service(self, service_name: str):
        """Reset rate limit for a service (admin operation)."""
        if service_name in self.request_log:
            del self.request_log[service_name]


class ServiceToServiceAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to authenticate service-to-service requests to Substrate API.

    Configuration via environment variables:
    - SUBSTRATE_SERVICE_SECRET: Shared secret for authentication
    - ALLOWED_SERVICES: Comma-separated list of allowed service names
    - SUBSTRATE_RATE_LIMIT_PER_SERVICE: Requests per minute per service (default: 1000)
    - ENABLE_SERVICE_AUTH: Enable/disable service auth (default: false for backward compat)

    Request headers expected:
    - Authorization: Bearer <service_secret>
    - X-Service-Name: <service_name>

    Exemptions:
    - Health check endpoints (/health, /health/*)
    - Public endpoints (configured in exempt_paths)
    - MCP endpoints (have their own auth)
    """

    def __init__(
        self,
        app,
        exempt_paths: Optional[set[str]] = None,
        exempt_prefixes: Optional[set[str]] = None,
    ):
        super().__init__(app)

        # Check if service auth is enabled (default: false for backward compatibility)
        self.enabled = os.getenv("ENABLE_SERVICE_AUTH", "false").lower() == "true"

        self.service_secret = os.getenv("SUBSTRATE_SERVICE_SECRET")
        if self.enabled and not self.service_secret:
            logger.warning(
                "ENABLE_SERVICE_AUTH=true but SUBSTRATE_SERVICE_SECRET not set - "
                "service auth will reject all requests!"
            )

        # Allowed service names
        allowed_services_str = os.getenv("ALLOWED_SERVICES", "platform-api,chatgpt-app")
        self.allowed_services = {s.strip() for s in allowed_services_str.split(",")}

        # Rate limiter
        rate_limit = int(os.getenv("SUBSTRATE_RATE_LIMIT_PER_SERVICE", "1000"))
        self.rate_limiter = ServiceRateLimiter(requests_per_minute=rate_limit)

        # Exempt paths (don't require service auth)
        self.exempt_paths = exempt_paths or {
            "/",
            "/health",
            "/health/db",
            "/health/queue",
            "/docs",
            "/openapi.json",
            "/favicon.ico",
            "/robots.txt",
        }

        self.exempt_prefixes = exempt_prefixes or {
            "/health",  # All health check endpoints
            "/api/mcp",  # MCP endpoints (have their own auth)
        }

        if self.enabled:
            logger.info(
                f"ServiceToServiceAuthMiddleware ENABLED: allowed_services={self.allowed_services}, "
                f"rate_limit={rate_limit}/min"
            )
        else:
            logger.info("ServiceToServiceAuthMiddleware DISABLED (ENABLE_SERVICE_AUTH=false)")

    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from service auth."""
        if path in self.exempt_paths:
            return True

        for prefix in self.exempt_prefixes:
            if path.startswith(prefix):
                return True

        return False

    async def dispatch(self, request: Request, call_next):
        """Process request and validate service authentication."""

        # If service auth disabled, pass through
        if not self.enabled:
            return await call_next(request)

        # Check if path is exempt
        if self._is_exempt(request.url.path):
            return await call_next(request)

        # Extract auth header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"Missing Authorization header from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate Bearer token
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format (expected Bearer token)",
            )

        token = auth_header[7:]  # Remove "Bearer " prefix
        if token != self.service_secret:
            logger.error(f"Invalid service token from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token",
            )

        # Extract service name
        service_name = request.headers.get("X-Service-Name")
        if not service_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing X-Service-Name header",
            )

        # Validate service name
        if service_name not in self.allowed_services:
            logger.error(f"Unauthorized service: {service_name}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Service '{service_name}' is not allowed",
            )

        # Check rate limit
        allowed, retry_after = self.rate_limiter.check_rate_limit(service_name)
        if not allowed:
            logger.warning(f"Rate limit exceeded for service: {service_name}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for service '{service_name}'",
                headers={"Retry-After": str(retry_after)} if retry_after else {},
            )

        # Attach service name to request state for logging
        request.state.service_name = service_name

        # Log authenticated service request
        logger.debug(
            f"Service request: {service_name} -> {request.method} {request.url.path}"
        )

        # Process request
        start_time = time.time()
        response = await call_next(request)
        latency_ms = (time.time() - start_time) * 1000

        # Log response
        logger.info(
            f"Service {service_name}: {request.method} {request.url.path} -> {response.status_code} ({latency_ms:.2f}ms)"
        )

        return response


def get_service_name(request: Request) -> Optional[str]:
    """
    Get authenticated service name from request.

    Returns:
        Service name or None if not authenticated
    """
    return getattr(request.state, "service_name", None)
