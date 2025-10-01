"""
Репозиторий пользователей.

Этот модуль содержит реализацию репозитория для работы с пользователями через
асинхронную сессию SQLAlchemy. Репозиторий отвечает за преобразование между
домашними сущностями и моделями базы данных, а также за типичные операции
CRUD.

Пример:
    Создание пользователя и получение по имени::

        from sqlalchemy.ext.asyncio import AsyncSession
        from domain.entities.base.user import User
        from domain.values.Username import UserName
        from infra.database.repositories.user_reposytory import UserRepository

        async def run(session: AsyncSession):
            repo = UserRepository(session)
            user = User(username=UserName("alice"), password_hash="hash")
            await repo.save(user)
            fetched = await repo.get_by_username(UserName("alice"))
            assert fetched is not None
"""

from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy import and_, func, select
from infra.database.repositories.base import BaseRepository
from infra.database.models import User as UserModel
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.base.user import User, UserRole
from domain.values.hashed_password import HashedPasswordSHA256
from domain.values.username import UserName
from infra.config import app_logger


class UserRepository(BaseRepository[User, UserModel]):
    """Репозиторий для управления сущностями пользователей.

    Репозиторий инкапсулирует доступ к базе данных и обеспечивает операции
    сохранения, обновления, удаления и выборки пользователей.

    Args:
        session: Асинхронная сессия SQLAlchemy, используемая для запросов.

    Пример:
        Создание экземпляра репозитория::

            from sqlalchemy.ext.asyncio import AsyncSession
            repo = UserRepository(session)  # type: ignore[name-defined]
    """

    def __init__(self, session: AsyncSession):
        """Инициализирует репозиторий.

        Args:
            session: Экземпляр ``AsyncSession`` для взаимодействия с БД.
        """
        super().__init__(session)

    def _to_entity(self, model: UserModel) -> User:
        """Преобразует модель БД в доменную сущность ``User``.

        Args:
            model: Модель пользователя уровня БД.

        Returns:
            Доменная сущность пользователя.
        """
        return User(
            id=str(model.id),
            username=UserName(model.username),
            password_hash=HashedPasswordSHA256(model.hashed_password),
            role=(
                UserRole(model.role.value) if hasattr(model, "role") else UserRole.USER
            ),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: User) -> UserModel:
        """Преобразует доменную сущность ``User`` в модель БД.

        Args:
            entity: Доменная сущность пользователя.

        Returns:
            Модель пользователя для сохранения в БД.
        """
        # Преобразуем доменную сущность в модель БД, учитывая различия в типах
        # и названиях полей (``hashed_password`` в модели БД).
        model_kwargs = {
            "username": entity.username.value if isinstance(entity.username, UserName) else entity.username,  # type: ignore[arg-type]
            "hashed_password": (
                entity.password_hash.value
                if isinstance(entity.password_hash, HashedPasswordSHA256)
                else str(entity.password_hash)
            ),
            "role": (
                entity.role.value
                if isinstance(entity.role, UserRole)
                else UserRole(str(entity.role.value))
            ),
            "is_active": entity.is_active,
        }

        # Если у сущности задан ``id`` (str UUID), передаём его в модель,
        # иначе позволяем БД сгенерировать значение по умолчанию.
        if getattr(entity, "id", None):
            model_kwargs["id"] = UUID(str(entity.id))

        return UserModel(**model_kwargs)

    async def _create(self, user: User) -> User:
        model = self._to_model(user)

        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)  # Получаем сгенерированные поля
        await self._session.commit()

        return self._to_entity(model)

    async def _update(self, user: User) -> User:
        model = await self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User with id {user.id} not found")

        model.username = user.username.value
        model.hashed_password = user.password_hash.value
        model.is_active = user.is_active
        model.role = user.role

        await self._session.flush()
        await self._session.refresh(model)
        await self._session.commit()

        return self._to_entity(model)

    async def save(self, user: User) -> User:
        """Сохраняет пользователя (создание или обновление).

        Если у сущности отсутствует ``id``, после сохранения метод
        заполняет поля ``id``, ``created_at`` и ``updated_at`` из модели БД.

        Args:
            user: Доменная сущность пользователя для сохранения.

        Returns:
            Обновлённая доменная сущность пользователя.

        Пример:
            Создание нового пользователя::

                user = User(username=UserName("bob"), password_hash="hash")
                saved = await repo.save(user)
                assert saved.id is not None
        """
        if user.id is None:
            # Создание нового пользователя
            return await self._create(user)
        else:
            # Обновление существующего пользователя
            return await self._update(user)

    async def update(self, user: User) -> User:
        """Обновляет пользователя.

        Args:
            user: Доменная сущность пользователя с изменёнными полями.

        Returns:
            Обновлённая доменная сущность пользователя.
        """
        if user.id is None:
            raise ValueError("Cannot update user without ID")

        return await self._update(user)

    async def delete(self, user_id: str) -> bool:
        """Удаляет пользователя по идентификатору.

        Args:
            user_id: Идентификатор пользователя в формате UUID (строка).

        Returns:
            ``True``, если пользователь найден и удалён, иначе ``False``.

        Пример:
            Удаление пользователя::

                ok = await repo.delete("7f3a2b7e-0d2e-4b2b-9a2a-2d4f7e9b5c1e")
                assert ok is True
        """
        query = select(UserModel).where(UserModel.id == UUID(user_id))
        result = await self._session.execute(query)
        await self._session.commit()
        model = result.scalar_one_or_none()

        if model:
            await self._session.delete(model)
            return True
        return False

    async def get_by_id(self, user_id: str) -> User | None:
        """Возвращает пользователя по идентификатору.

        Args:
            user_id: Идентификатор пользователя в формате UUID (строка).

        Returns:
            Объект ``User`` или ``None``, если запись не найдена.
        """
        model = await self._session.get(UserModel, user_id)
        return self._to_entity(model) if model else None

    async def get_by_username(self, username: UserName) -> User | None:
        """Возвращает пользователя по имени пользователя.

        Args:
            username: Значение типа ``UserName``.

        Returns:
            Объект ``User`` или ``None``, если запись не найдена.
        """
        query = select(UserModel).where(UserModel.username == username.value)
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

        return self._to_entity(model) if model else None

    async def exists_with_username(self, username: UserName) -> bool:
        """Проверяет существование пользователя с указанным именем.

        Args:
            username: Значение типа ``UserName``.

        Returns:
            ``True``, если пользователь существует, иначе ``False``.

        Пример:
            Проверка существования::

                exists = await repo.exists_with_username(UserName("alice"))
                assert isinstance(exists, bool)
        """
        query = select(UserModel.id).where(UserModel.username == username.value)
        result = await self._session.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_all(
        self,
        limit: int = 50,
        offset: int = 0,
        is_active: Optional[bool] = None,
        role: Optional[UserRole] = None,
    ) -> List[User]:
        """Возвращает список пользователей с пагинацией и фильтрацией.

        Args:
            limit: Максимальное количество пользователей для возврата.
            offset: Смещение для пагинации.
            is_active: Фильтр по активности пользователя.
            role: Фильтр по роли пользователя.

        Returns:
            Кортеж (список пользователей, общее количество).

        Example:
            Получение активных пользователей::

                users, total = await repo.get_all_users(
                    limit=10,
                    offset=0,
                    is_active=True,
                    role=UserRole.USER
                )
        """
        # Базовый запрос для получения данных
        base_query = select(UserModel)

        # Применяем фильтры
        conditions = []

        if is_active is not None:
            conditions.append(UserModel.is_active == is_active)

        if role is not None:
            conditions.append(UserModel.role == role)

        if conditions:
            base_query = base_query.where(and_(*conditions))

        # Запрос для получения общего количества (без пагинации)
        count_query = select(func.count()).select_from(UserModel)
        if conditions:
            count_query = count_query.where(and_(*conditions))

        # Выполняем запрос на количество
        count_result = await self._session.execute(count_query)
        total = count_result.scalar_one()

        # Запрос для получения данных с пагинацией
        data_query = base_query.offset(offset).limit(limit)

        # Выполняем запрос на данные
        result = await self._session.execute(data_query)
        models = result.scalars().all()

        # Преобразуем модели в сущности
        users = [self._to_entity(model) for model in models]

        return users, total
