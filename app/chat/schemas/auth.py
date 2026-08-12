from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., max_length=20, description="The username of the user")
    password: str = Field(..., description="The password of the user")

class UserLogin(BaseModel):
    username: str = Field(..., max_length=20, description="The username of the user")
    password: str = Field(..., description="The password of the user")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True
