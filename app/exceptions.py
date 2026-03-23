"""
Domain exceptions and FastAPI exception handlers.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse


class PlatformError(Exception):
    """Base class for all domain errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: Optional[str] = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class NotFoundError(PlatformError):
    status_code = 404
    error_code = "NOT_FOUND"


class ConflictError(PlatformError):
    status_code = 409
    error_code = "CONFLICT"


class ValidationError(PlatformError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class OpenStackError(PlatformError):
    """Wraps unexpected errors from openstacksdk."""
    status_code = 502
    error_code = "OPENSTACK_ERROR"


class QuotaExceededError(PlatformError):
    status_code = 429
    error_code = "QUOTA_EXCEEDED"


def _error_body(exc: PlatformError) -> dict:
    body: dict = {"error": exc.error_code, "message": exc.message}
    if exc.detail:
        body["detail"] = exc.detail
    return body


async def platform_error_handler(request: Request, exc: PlatformError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=_error_body(exc))


def register_exception_handlers(app) -> None:  # noqa: ANN001
    app.add_exception_handler(PlatformError, platform_error_handler)
