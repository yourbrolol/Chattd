from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.chat.schemas.applications import (
    ApplicationApply,
    ApplicationReview,
    ApplicationResponse,
    PendingApplicationItem
)

router = APIRouter(prefix="/applications", tags=["applications"])

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_to_room(apply_data: ApplicationApply):
    pass

@router.post("/{application_id}/review", response_model=ApplicationResponse)
async def review_application(application_id: int, review_data: ApplicationReview):
    pass

@router.get("/pending", response_model=List[PendingApplicationItem])
async def pending_applications():
    pass

@router.get("/pending/{room_name}", response_model=List[PendingApplicationItem])
async def room_pending_applications(room_name: str):
    pass
