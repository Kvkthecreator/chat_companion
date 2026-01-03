"""Security headers middleware for clickjacking and other protections."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses.

    Protects against:
    - Clickjacking (X-Frame-Options, Content-Security-Policy frame-ancestors)
    - MIME type sniffing (X-Content-Type-Options)
    - XSS in older browsers (X-XSS-Protection)
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevent clickjacking - deny all framing
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy - don't leak full URL to other origins
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
