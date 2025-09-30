from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database.repositories.user_reposytory import UserRepository
from infra.security import PasswordAuthenticationService, JWTService
from infra.config import settings
from application.services.user_service import UserApplicationService
from application.api.dependencies.auth import get_db_session
from domain.entities.base.user import UserRole


security = HTTPBearer()


def get_user_service(
    session: AsyncSession = Depends(get_db_session),
) -> UserApplicationService:
    user_repo = UserRepository(session)
    password_service = PasswordAuthenticationService()
    return UserApplicationService(user_repo, password_service)


def get_jwt_handler() -> JWTService:
    return JWTService(
        access_token_expire_minutes=settings.secrurity.access_token_expire_minutes,
        refresh_token_expire_minutes=settings.secrurity.refresh_token_expire_minutes,
        secret_key=settings.secrurity.secret_key,
        algorithm=settings.secrurity.algorithm,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_handler: JWTService = Depends(get_jwt_handler),
    user_service: UserApplicationService = Depends(get_user_service),
):
    """
    Извлекает текущего пользователя из JWT токена.
    """
    token = credentials.credentials
    payload = jwt_handler.verify_token(token)

    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = await user_service.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


async def require_admin(
    current_user=Depends(get_current_user),
):
    """
    Проверяет, что текущий пользователь имеет роль ADMIN.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
