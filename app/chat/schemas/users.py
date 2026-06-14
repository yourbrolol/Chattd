from pydantic import BaseModel, Field
from typing import Optional

class UserProfileResponse(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None

class SettingsEditResponse(BaseModel):
    success: bool
    avatar_url: Optional[str] = None
