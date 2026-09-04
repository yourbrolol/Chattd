"""Central error catalog: user-safe messages + dev-friendly codes.

Convention:
- Services/routers raise AppError subclasses, never raw HTTPException with
  ad-hoc sentence details.
- The exception handler (see app/main.py) logs the full traceback with a
  request_id for devs, and returns only { error: {code, message}, request_id }
  to users. `detail` (== code) is kept for backwards compat with old clients/tests.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorCode:
    AUTH_REQUIRED = "auth_required"
    INVALID_CREDENTIALS = "invalid_credentials"
    USERNAME_TAKEN = "username_taken"
    BAD_REQUEST = "bad_request"  # prohibited characters etc.
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"
    NOT_MEMBER = "not_member"
    USER_NOT_MEMBER = "user_not_member"
    ALREADY_MEMBER = "already_member"
    EMPTY_NAME = "empty_name"
    EMPTY_USERNAME = "empty_username"
    NAME_TAKEN = "name_taken"
    NO_CHANGES = "no_changes"
    FILE_TOO_LARGE = "file_too_large"
    INVALID_FORMAT = "invalid_format"
    INVALID_ACTION = "invalid_action"
    APP_REQUIRED = "app_required"
    APP_PENDING = "app_pending"
    UNKNOWN = "unknown_error"
    CREATE_FAILED = "create_failed"
    NETWORK = "network"


# User-facing sentences. Devs: add a code here once, reuse everywhere.
USER_MESSAGES = {
    ErrorCode.AUTH_REQUIRED: "You must be logged in.",
    ErrorCode.INVALID_CREDENTIALS: "Invalid username or password.",
    ErrorCode.USERNAME_TAKEN: "This username is already taken.",
    ErrorCode.BAD_REQUEST: "Invalid characters in username or password.",
    ErrorCode.NOT_FOUND: "Not found.",
    ErrorCode.FORBIDDEN: "You don't have permission to do that.",
    ErrorCode.NOT_MEMBER: "You are not a member of this room.",
    ErrorCode.USER_NOT_MEMBER: "That user is not a member of this room.",
    ErrorCode.ALREADY_MEMBER: "You are already a member.",
    ErrorCode.EMPTY_NAME: "Room name cannot be empty.",
    ErrorCode.EMPTY_USERNAME: "Username cannot be empty.",
    ErrorCode.NAME_TAKEN: "That name is already taken.",
    ErrorCode.NO_CHANGES: "No changes detected.",
    ErrorCode.FILE_TOO_LARGE: "File size exceeds the limit of 2MB.",
    ErrorCode.INVALID_FORMAT: "Invalid file format. Only PNG, JPG, JPEG, GIF, and WEBP are allowed.",
    ErrorCode.INVALID_ACTION: "Invalid action. Use 'approve' or 'reject'.",
    ErrorCode.APP_REQUIRED: "This is a private room. You need to apply for membership.",
    ErrorCode.APP_PENDING: "Your application is pending. Please wait for the owner to review it.",
    ErrorCode.UNKNOWN: "Something went wrong. Please try again.",
    ErrorCode.CREATE_FAILED: "Could not create. Please try again.",
    ErrorCode.NETWORK: "Network error. Please try again.",
}


class AppError(Exception):
    code: str = ErrorCode.UNKNOWN
    status: int = 400

    def __init__(self, code: str | None = None, message: str | None = None, status: int | None = None):
        self.code = code or self.code
        self.status = status if status is not None else self.status
        # User-safe message only; never include tracebacks/SQL here.
        self.user_message = message or USER_MESSAGES.get(self.code, USER_MESSAGES[ErrorCode.UNKNOWN])
        super().__init__(f"[{self.status} {self.code}] {self.user_message}")


class AuthRequired(AppError):
    code = ErrorCode.AUTH_REQUIRED
    status = 401


class InvalidCredentials(AppError):
    code = ErrorCode.INVALID_CREDENTIALS
    status = 400


class UsernameTaken(AppError):
    code = ErrorCode.USERNAME_TAKEN
    status = 400


class BadRequest(AppError):
    code = ErrorCode.BAD_REQUEST
    status = 422


class NotFound(AppError):
    code = ErrorCode.NOT_FOUND
    status = 404


class Forbidden(AppError):
    code = ErrorCode.FORBIDDEN
    status = 403


class NotMember(AppError):
    code = ErrorCode.NOT_MEMBER
    status = 403


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Dev view -> logs; user view -> safe envelope. Keeps `detail` for old clients."""
    request_id = uuid.uuid4().hex[:8]
    # Dev-only: full traceback + path in server logs.
    logger.error("%s %s %s %s", request_id, request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=exc.status,
        content={
            "error": {"code": exc.code, "message": exc.user_message},
            "request_id": request_id,
            "detail": exc.code,  # backwards compat: old tests/clients read `detail`
        },
    )
