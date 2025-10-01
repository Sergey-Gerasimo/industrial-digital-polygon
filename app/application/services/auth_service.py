from math import exp
from typing import Optional
from uuid import UUID
from domain.entities.base import User
from domain.values import UserName
from domain.exceptions.user import InvalidCredentials, UserNotActive
from infra.database.repositories import UserRepository
from infra.security import PasswordAuthenticationService, JWTService


class AuthApplicationService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordAuthenticationService,
        jwt_service: JWTService,
    ):
        self._user_repository = user_repository
        self._password_service = password_service
        self._jwt_service = jwt_service

    async def authenticate_user(
        self,
        username: str,
        password: str,
        access_expire_in: Optional[int] = None,
        refresh_expire_in: Optional[int] = None,
    ) -> tuple[User, str, str]:
        """Application operation for user authentication"""
        username_value = UserName(username)
        user = await self._user_repository.get_by_username(username_value)

        if not user:
            raise InvalidCredentials()

        if not user.is_active:
            raise UserNotActive(user_id=str(user.id))

        password_valid = self._password_service.verify_password(
            password, user.password_hash
        )

        if not password_valid:
            raise InvalidCredentials()
        # Generate tokens
        access_token = self._jwt_service.create_access_token(
            subject=str(user.id), expires_delta=access_expire_in
        )
        refresh_token = self._jwt_service.create_refresh_token(
            subject=str(user.id), expires_delta=refresh_expire_in
        )

        return user, access_token, refresh_token

    async def refresh_tokens(
        self,
        refresh_token: str,
        access_expire_in: Optional[int] = None,
        refresh_expire_in: Optional[int] = None,
    ) -> tuple[str, str]:
        """Application operation for refreshing tokens"""
        user_id = self._jwt_service.validate_refresh_token(refresh_token)
        user = await self._user_repository.get_by_id(UUID(user_id))

        if not user or not user.is_active:
            raise InvalidCredentials()

        new_access_token = self._jwt_service.create_access_token(
            subject=str(user.id), expires_delta=access_expire_in
        )
        new_refresh_token = self._jwt_service.create_refresh_token(
            subject=str(user.id), expires_delta=refresh_expire_in
        )

        return new_access_token, new_refresh_token

    async def get_current_user(self, token: str) -> User:
        """Application operation for getting current user from token"""
        user_id = self._jwt_service.validate_access_token(token)
        user = await self._user_repository.get_by_id(UUID(user_id))

        if not user or not user.is_active:
            raise InvalidCredentials()

        return user
