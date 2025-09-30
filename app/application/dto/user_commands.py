from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from domain.enums import UserRole


# Commands
class CreateUserCommand(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER


class UpdateUserUsernameCommand(BaseModel):
    user_id: UUID
    new_username: str = Field(..., min_length=3, max_length=50)


class UpdateUserPasswordCommand(BaseModel):
    user_id: UUID
    new_password: str = Field(..., min_length=6)


class UpdateUserRoleCommand(BaseModel):
    user_id: UUID
    new_role: UserRole


class ChangeUserStatusCommand(BaseModel):
    user_id: UUID


# Queries
class GetUserQuery(BaseModel):
    user_id: UUID


class GetUserByUsernameQuery(BaseModel):
    username: str


class ListUsersQuery(BaseModel):
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
