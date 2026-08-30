from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.settings import settings

# --- Request Schemas ---

class RoomCreate(BaseModel):
    room_name: str = Field(
        ...,
        min_length=settings.ROOM_NAME_MIN_LENGTH,
        max_length=settings.ROOM_NAME_MAX_LENGTH,
        pattern=settings.ROOM_NAME_PATTERN,
        description="The name of the room to create"
    )
    room_type: str = Field(..., description="The type of the room (e.g., public, private)")

class RoomSearch(BaseModel):
    q: str = Field(..., description="Search query matching room names")

class JoinRoom(BaseModel):
    room_name: str = Field(..., description="The name of the room to join")

class EditRoom(BaseModel):
    name: str = Field(
        ...,
        min_length=settings.ROOM_NAME_MIN_LENGTH,
        max_length=settings.ROOM_NAME_MAX_LENGTH,
        pattern=settings.ROOM_NAME_PATTERN,
        description="The new name of the room"
    )

class KickRoomMember(BaseModel):
    username: str = Field(..., description="The username of the member to kick")

# --- Response Schemas (Optional but recommended for strict typing) ---

class RoomListItem(BaseModel):
    id: int
    name: str
    room_type: str

class RoomMember(BaseModel):
    id: Optional[int]
    username: str
    role: str
    avatar: Optional[str] = None

class RoomDetailsResponse(BaseModel):
    id: int
    name: str
    room_type: str
    owner: Optional[str] = None
    members_data: List[RoomMember]