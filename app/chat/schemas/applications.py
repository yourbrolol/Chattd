from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ApplicationApply(BaseModel):
    room_name: str = Field(..., description="Name of the room to apply to")

class ApplicationReview(BaseModel):
    action: str = Field(..., description="Action to take: approve or reject")

class ApplicationResponse(BaseModel):
    id: int
    room: str
    status: str

class PendingApplicationItem(BaseModel):
    id: int
    room: str
    applicant: Optional[str] = None
    created_at: str
