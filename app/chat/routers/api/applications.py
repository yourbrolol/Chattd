from fastapi import Depends, status
from fastapi.responses import JSONResponse
from app.core.router import APIRouter
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import get_current_user
from app.chat.models import User, ChatRoom
from app.chat.schemas.applications import (
    ApplicationApply,
    ApplicationReview,
    ApplicationResponse,
    PendingApplicationItem
)
from app.chat.services import applications as apps_service
from app.chat.errors import AppError, ErrorCode

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def apply_to_room(
    apply_data: ApplicationApply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app, code = await apps_service.apply_to_room(db, apply_data.room_name, current_user)

    if code == apps_service.APP_AUTH_REQUIRED:
        raise AppError(ErrorCode.AUTH_REQUIRED, status=401)
    if code == apps_service.APP_NOT_FOUND:
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if code == apps_service.APP_ALREADY_MEMBER:
        raise AppError(ErrorCode.ALREADY_MEMBER, status=400)
    if code in (apps_service.APP_ALREADY_APPROVED, apps_service.APP_ALREADY_PENDING):
        # Idempotent re-apply: normal 200, not an error. Frontend checks `result`.
        # NOTE: route default is 201, so set 200 explicitly.
        outcome = "already_approved" if code == apps_service.APP_ALREADY_APPROVED else "already_pending"
        return JSONResponse(
            status_code=200,
            content={
                "id": app.id,
                "room": apply_data.room_name,
                "status": app.status.value,
                "result": outcome,
            },
        )
    if not app:
        raise AppError(ErrorCode.UNKNOWN, status=400)

    return {
        "id": app.id,
        "room": apply_data.room_name,
        "status": app.status.value,
        "result": "created",
    }

@router.post("/{application_id}/review", response_model=ApplicationResponse)
async def review_application(
    application_id: int,
    review_data: ApplicationReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    action = review_data.action.strip().lower()
    if action not in ("approve", "reject"):
        raise AppError(ErrorCode.INVALID_ACTION, status=400)

    approve = action == "approve"
    app, room_name, error = await apps_service.review_application(db, application_id, current_user, approve)

    if error == apps_service.APP_NOT_FOUND:
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if error == "forbidden":
        raise AppError(ErrorCode.FORBIDDEN, status=403)

    return {
        "id": app.id,
        "room": room_name,
        "status": app.status.value
    }

@router.get("/pending", response_model=List[PendingApplicationItem])
async def pending_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await apps_service.get_pending_applications_for_owner(db, current_user)

@router.get("/pending/{room_name}", response_model=List[PendingApplicationItem])
async def room_pending_applications(
    room_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    apps, error = await apps_service.get_pending_applications_for_room(db, room_name, current_user)
    if error == "room_not_found":
        raise AppError(ErrorCode.NOT_FOUND, status=404)
    if error == "forbidden":
        raise AppError(ErrorCode.FORBIDDEN, status=403)
    return apps or []
