from pydantic import BaseModel, ConfigDict

from app.infrastructure.api.schemas.user_schema import UserResponse


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginData(BaseModel):
    user: UserResponse
    token: str

    model_config = ConfigDict(from_attributes=True)
