from pydantic import BaseModel, Field, ConfigDict
from app.core.settings import settings

class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=settings.USERNAME_MIN_LENGTH,
        max_length=settings.USERNAME_MAX_LENGTH,
        description="The username of the user",
    )
    password: str = Field(
        ...,
        min_length=settings.PASSWORD_MIN_LENGTH,
        max_length=settings.PASSWORD_MAX_LENGTH,
        description="The password of the user",
    )

class UserLogin(BaseModel):
    username: str = Field(
        ...,
        min_length=settings.USERNAME_MIN_LENGTH,
        max_length=settings.USERNAME_MAX_LENGTH,
        description="The username of the user",
    )
    password: str = Field(
        ...,
        min_length=settings.PASSWORD_MIN_LENGTH,
        max_length=settings.PASSWORD_MAX_LENGTH,
        description="The password of the user",
    )

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(
        from_attributes = True
    )