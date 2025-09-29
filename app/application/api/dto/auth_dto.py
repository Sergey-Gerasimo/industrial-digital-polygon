"""
DTO (Data Transfer Objects) для эндпоинтов регистрации и логина FastAPI.

Содержит Pydantic-схемы для входящих и исходящих данных при регистрации и
аутентификации пользователей.

Пример:
    Использование в FastAPI роутере::

        from fastapi import APIRouter
        from app.application.api.dto.auth_dto import (
            RegisterUserRequest, RegisterUserResponse, LoginRequest, LoginResponse
        )

        router = APIRouter()

        @router.post("/auth/register", response_model=RegisterUserResponse)
        async def register(payload: RegisterUserRequest):
            ...

        @router.post("/auth/login", response_model=LoginResponse)
        async def login(payload: LoginRequest):
            ...
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, constr, model_validator

from infra.database.models import UserRole


UsernameStr = constr(min_length=3, max_length=50)
PasswordStr = constr(min_length=8, max_length=255)


class RegisterUserRequest(BaseModel):
    """Входная схема данных для регистрации пользователя.

    Args:
        username: Имя пользователя (3-50 символов).
        password: Пароль (минимум 8 символов).
        password_confirm: Подтверждение пароля; должно совпадать с ``password``.

    Raises:
        ValueError: Если пароли не совпадают.
    """

    username: UsernameStr = Field(..., description="Имя пользователя")
    password: PasswordStr = Field(..., description="Пароль")
    password_confirm: PasswordStr = Field(..., description="Подтверждение пароля")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "username": "alice",
                    "password": "StrongPass!123",
                    "password_confirm": "StrongPass!123",
                }
            ]
        }
    )

    @model_validator(mode="after")
    def _validate_passwords_match(self) -> "RegisterUserRequest":
        if self.password != self.password_confirm:
            raise ValueError("Пароли не совпадают")
        return self


class RegisterUserResponse(BaseModel):
    """Выходная схема данных после регистрации пользователя.

    Args:
        id: Идентификатор пользователя (UUID).
        username: Имя пользователя.
        is_active: Флаг активности пользователя.
        created_at: Дата создания пользователя.
    """

    id: UUID = Field(..., description="UUID пользователя")
    username: str = Field(..., description="Имя пользователя")
    is_active: bool = Field(True, description="Активен ли пользователь")
    role: UserRole = Field(UserRole.USER, description="Роль пользователя")
    created_at: Optional[datetime] = Field(None, description="Дата создания")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "7f3a2b7e-0d2e-4b2b-9a2a-2d4f7e9b5c1e",
                    "username": "alice",
                    "is_active": True,
                    "created_at": "2025-01-01T12:00:00",
                    "role": "user",
                }
            ]
        }
    )


class LoginRequest(BaseModel):
    """Входная схема данных для логина.

    Args:
        username: Имя пользователя (3-50 символов).
        password: Пароль (минимум 8 символов).
    """

    username: UsernameStr = Field(..., description="Имя пользователя")
    password: PasswordStr = Field(..., description="Пароль")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"username": "alice", "password": "StrongPass!123"}]
        }
    )


class LoginResponse(BaseModel):
    """Выходная схема данных для успешной аутентификации.

    Args:
        access_token: Токен доступа (JWT).
        token_type: Тип токена (обычно ``Bearer``).
        expires_in: Время жизни токена в секундах (опционально).
    """

    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field("Bearer", description="Тип токена")
    expires_in: Optional[int] = Field(None, description="Время жизни токена в секундах")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                }
            ]
        }
    )


class RefreshTokenRequest(BaseModel):
    """Входная схема для обновления access токена.

    Args:
        refresh_token: Действительный refresh токен
    """

    refresh_token: str = Field(..., description="JWT refresh токен")


class RefreshTokenResponse(BaseModel):
    """Выходная схема данных для операции обновления токена.

    Args:
        access_token: Новый JWT токен доступа
        token_type: Тип токена
        expires_in: Время жизни токена в секундах (опционально)
    """

    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field("Bearer", description="Тип токена")
    expires_in: Optional[int] = Field(None, description="Время жизни токена в секундах")
