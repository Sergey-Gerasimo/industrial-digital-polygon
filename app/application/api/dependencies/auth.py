from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database.database import AsyncSessionLocal
from infra.database.repositories.user_reposytory import UserRepository
from infra.security import PasswordAuthenticationService, JWTService
from infra.config import settings
from application.services import AuthApplicationService


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:  # type: ignore[call-arg]
        yield session


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> AuthApplicationService:
    user_repo = UserRepository(session)
    password_service = PasswordAuthenticationService()
    jwt_service = JWTService(
        access_token_expire_minutes=settings.secrurity.access_token_expire_minutes,
        refresh_token_expire_minutes=settings.secrurity.refresh_token_expire_minutes,
        secret_key=settings.secrurity.secret_key,
        algorithm=settings.secrurity.algorithm,
    )
    return AuthApplicationService(user_repo, password_service, jwt_service)
