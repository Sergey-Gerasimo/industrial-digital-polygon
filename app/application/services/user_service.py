from typing import List, Optional

from infra.database.repositories.user_reposytory import UserRepository
from infra.security import PasswordAuthenticationService
from domain.entities.base.user import User, UserRole
from domain.values.username import UserName


class UserApplicationService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_service: PasswordAuthenticationService,
    ):
        self._user_repository = user_repository
        self._password_service = password_service

    async def create(
        self,
        username: str,
        password: str,
        role: UserRole = UserRole.USER,
        is_active: bool = True,
    ) -> User:
        if await self._user_repository.exists_with_username(UserName(username)):
            raise ValueError("Username already taken")
        password_hash = self._password_service.hash_password(password)
        user = User(
            username=UserName(username),
            password_hash=password_hash,
            role=role,
            is_active=is_active,
        )
        return await self._user_repository.save(user)

    async def get(self, user_id: str) -> Optional[User]:
        return await self._user_repository.get_by_id(user_id)

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self._user_repository.get_by_username(UserName(username))

    async def list(self, limit: int = 50, offset: int = 0) -> List[User]:
        # Простейшая реализация на базе прямого select в репозитории пока отсутствует.
        # Для полноты можно добавить метод в репозиторий; временно вернём пустой список.
        return []

    async def update(
        self,
        user_id: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
    ) -> User:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        if username is not None and username != user.username.value:
            if await self._user_repository.exists_with_username(UserName(username)):
                raise ValueError("Username already taken")
            user = User(
                username=UserName(username),
                password_hash=user.password_hash,
                role=user.role,
                is_active=user.is_active,
                id=user.id,
            )

        if password is not None:
            password_hash = self._password_service.hash_password(password)
            user = User(
                username=user.username,
                password_hash=password_hash,
                role=user.role,
                is_active=user.is_active,
                id=user.id,
            )

        if role is not None and role != user.role:
            user = User(
                username=user.username,
                password_hash=user.password_hash,
                role=role,
                is_active=user.is_active,
                id=user.id,
            )

        if is_active is not None and is_active != user.is_active:
            user = User(
                username=user.username,
                password_hash=user.password_hash,
                role=user.role,
                is_active=is_active,
                id=user.id,
            )

        return await self._user_repository.save(user)

    async def delete(self, user_id: str) -> bool:
        return await self._user_repository.delete(user_id)
