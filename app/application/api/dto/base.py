from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


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
