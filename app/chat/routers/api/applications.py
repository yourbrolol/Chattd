from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_room(
    apply_data: ApplicationApply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app, code = await apps_service.apply_to_room(db, apply_data.room_name, current_user)
    
    if code == apps_service.APP_AUTH_REQUIRED:
        raise HTTPException(status_code=401, detail="auth_required")
    if code == apps_service.APP_NOT_FOUND:
        raise HTTPException(status_code=404, detail="not_found")
    if code == apps_service.APP_ALREADY_MEMBER:
        raise HTTPException(status_code=400, detail="already_member")
    if code == apps_service.APP_ALREADY_APPROVED:
        raise HTTPException(status_code=200, detail="already_approved")
    if code == apps_service.APP_ALREADY_PENDING:
        raise HTTPException(status_code=200, detail="already_pending")
    if not app:
        raise HTTPException(status_code=400, detail="unknown_error")
        
    room_name = app.room.name if getattr(app, "room", None) else ""

    return {
        "id": app.id,
        "room": room_name,
        "status": app.status.value
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
        raise HTTPException(status_code=400, detail="invalid_action")

    approve = action == "approve"
    app, error = await apps_service.review_application(db, application_id, current_user, approve)
    
    if error == apps_service.APP_NOT_FOUND or app is None:
        raise HTTPException(status_code=404, detail="not_found")
    if error == "forbidden":
        raise HTTPException(status_code=403, detail="forbidden")

    room_name = app.room.name if getattr(app, "room", None) else ""

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
        raise HTTPException(status_code=404, detail="room not found")
    if error == "forbidden":
        raise HTTPException(status_code=403, detail="forbidden")
    return apps or []
