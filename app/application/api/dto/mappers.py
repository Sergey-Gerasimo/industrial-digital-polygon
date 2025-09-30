from typing import Any
from .user_dto import UserResponse
from .auth_dto import AuthResponse
from infra.database.models import User


def user_to_response(user: User) -> UserResponse:
    """Конвертирует SQLAlchemy User в UserResponse"""
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def create_auth_response(user: User, tokens: dict) -> AuthResponse:
    """Создает AuthResponse для регистрации/логина"""

    return AuthResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=user_to_response(user),
        message="Operation successful",
    )
