"""Domain exceptions and their HTTP translation.

Services raise these domain exceptions; route handlers stay thin. A single set
of exception handlers maps them to the API error envelope
``{"detail": "<safe message>", "code": "<machine_code>"}`` (see docs/API.md).
Internal details never reach the client.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

log = get_logger(__name__)


class AppError(Exception):
    """Base class for expected, client-safe domain errors."""

    status_code: int = 400
    code: str = "app_error"
    message: str = "Request could not be processed."

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        self.message = message or self.message
        if code is not None:
            self.code = code
        super().__init__(self.message)


class ValidationError(AppError):
    status_code = 400
    code = "validation_error"
    message = "The request was invalid."


class AuthenticationError(AppError):
    status_code = 401
    code = "unauthenticated"
    message = "Authentication is required."


class AuthorizationError(AppError):
    status_code = 403
    code = "forbidden"
    message = "You are not allowed to perform this action."


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "The requested resource was not found."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "The request conflicts with the current state."


def _envelope(status_code: int, detail: str, code: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail, "code": code})


def register_exception_handlers(app: FastAPI) -> None:
    """Attach JSON-envelope exception handlers to the app."""

    @app.exception_handler(AppError)
    async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return _envelope(exc.status_code, exc.message, exc.code)

    @app.exception_handler(RequestValidationError)
    async def _request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed.",
                "code": "request_validation_error",
                "errors": jsonable_encoder(exc.errors()),
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Preserve any string detail but always surface a machine code.
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return _envelope(exc.status_code, detail, f"http_{exc.status_code}")

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        log.error(
            "unhandled_exception",
            path=request.url.path,
            method=request.method,
            exc_info=exc,
        )
        return _envelope(500, "An internal error occurred.", "internal_error")
