import os
import secrets
import logging

from fastapi import Request
from starlette.responses import JSONResponse
from app.chat.errors import AppError, ErrorCode, USER_MESSAGES
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import parse_qs

from app.core.config import CSRF_MAX_AGE

logger = logging.getLogger(__name__)

CSRF_COOKIE_NAME = "csrf_token"


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _get_csrf_header_token(request: Request) -> str | None:
    # Browsers/clients may send either spelling; check both.
    return request.headers.get("x-csrftoken") or request.headers.get("x-csrf-token")


def _parse_form_token(body: bytes, content_type: str) -> str | None:
    if "application/x-www-form-urlencoded" in content_type:
        parsed = parse_qs(body.decode("utf-8", errors="replace"))
        values = parsed.get(CSRF_COOKIE_NAME)
        return values[0] if values else None
    return None


def _forbidden_response() -> JSONResponse:
    # NOTE: raising inside BaseHTTPMiddleware.dispatch is NOT caught by
    # app exception handlers, so return the same envelope directly.
    return JSONResponse(
        status_code=403,
        content={
            "error": {"code": ErrorCode.FORBIDDEN, "message": USER_MESSAGES[ErrorCode.FORBIDDEN]},
            "detail": ErrorCode.FORBIDDEN,
        },
    )


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Tests (TESTING=true) don't send CSRF tokens; bypass there only.
        if os.getenv("TESTING") == "true":
            return await call_next(request)
        # WebSocket connections authenticate via the access_token cookie only.
        # BaseHTTPMiddleware already skips non-http scopes; guard explicitly too.
        if request.scope.get("type") != "http":
            return await call_next(request)

        if request.method in ("GET", "HEAD", "OPTIONS"):
            if CSRF_COOKIE_NAME not in request.cookies:
                token = _generate_token()
                response = await call_next(request)
                response.set_cookie(
                    key=CSRF_COOKIE_NAME,
                    value=token,
                    max_age=CSRF_MAX_AGE,
                    httponly=False,
                    samesite="lax",
                    path="/",
                )
                return response
            return await call_next(request)

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)

        # 1. Check X-CSRFToken header (AJAX / fetch requests)
        header_token = _get_csrf_header_token(request)
        if header_token:
            if not cookie_token or cookie_token != header_token:
                return _forbidden_response()
            return await call_next(request)

        # 2. Check form body (plain HTML form submissions)
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type:
            body = await request.body()
            form_token = _parse_form_token(body, content_type)
            if form_token and cookie_token and cookie_token == form_token:
                return await call_next(request)

        return _forbidden_response()


async def get_csrf_token(request: Request) -> str:
    """Dependency for frontend form routes. Validates the form csrf_token field against the cookie."""
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    form = await request.form()
    form_token = form.get(CSRF_COOKIE_NAME)

    if not cookie_token or not form_token or cookie_token != form_token:
        raise AppError(ErrorCode.FORBIDDEN, status=403)

    return cookie_token
