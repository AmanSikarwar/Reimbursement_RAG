"""
Security middleware for the FastAPI application.

Provides security headers, rate limiting, and request validation.
"""

import time
from collections import defaultdict
from typing import Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )

        # Add HSTS header for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.clients: Dict[str, list] = defaultdict(list)

    def get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Use X-Forwarded-For header if behind a proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Fallback to direct client IP
        client_host = getattr(request.client, "host", "unknown")
        return client_host

    async def dispatch(self, request: Request, call_next):
        client_id = self.get_client_id(request)
        current_time = time.time()

        # Clean old requests (older than 1 minute)
        self.clients[client_id] = [
            req_time
            for req_time in self.clients[client_id]
            if current_time - req_time < 60
        ]

        # Check rate limit
        if len(self.clients[client_id]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.requests_per_minute} per minute",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        # Add current request
        self.clients[client_id].append(current_time)

        response = await call_next(request)

        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - len(self.clients[client_id]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for additional request validation."""

    async def dispatch(self, request: Request, call_next):
        # Validate content length
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                max_size = settings.max_file_size_bytes * 2  # Allow some overhead
                if length > max_size:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Request too large",
                            "message": "Request size exceeds maximum allowed size",
                            "max_size_mb": settings.MAX_FILE_SIZE,
                        },
                    )
            except ValueError:
                pass

        # Validate content type for upload endpoints
        if request.url.path.startswith("/api/v1/analyze-invoices"):
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("multipart/form-data"):
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid content type",
                        "message": "Upload endpoints require multipart/form-data",
                    },
                )

        return await call_next(request)
