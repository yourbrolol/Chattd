from pydantic import BaseModel, Field, ConfigDict

class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=20, description="The username of the user")
    password: str = Field(..., min_length=1, description="The password of the user")

class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=20, description="The username of the user")
    password: str = Field(..., min_length=1, description="The password of the user")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(
        from_attributes = True
    )