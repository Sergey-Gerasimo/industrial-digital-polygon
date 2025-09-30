from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Username for login")
    password: str = Field(..., min_length=1, description="Password for login")


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1, description="Refresh token")


class TokenResponse(BaseResponse):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expire_in: int


class RegisterRequest(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=50, description="Username for registration"
    )
    password: str = Field(..., min_length=6, description="Password for registration")


class AuthResponse(TokenResponse):
    user: "UserResponse"


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(
        ..., min_length=6, max_length=100, description="New password"
    )


class ErrorResponse(BaseResponse):
    success: bool = False
    error: str
    status_code: int
    details: Optional[dict] = None


class SuccessResponse(BaseResponse):
    data: Optional[dict] = None


class LogoutResponse(BaseResponse):
    message: str = "Successfully logged out"


class MessageResponse(BaseResponse):
    message: str


from .user_dto import UserResponse

# Обновляем AuthResponse после импорта UserResponse
AuthResponse.model_rebuild()
