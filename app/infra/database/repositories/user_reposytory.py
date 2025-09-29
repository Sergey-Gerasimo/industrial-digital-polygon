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

from uuid import UUID
from sqlalchemy import select
from infra.database.repositories.base import BaseRepository
from infra.database.models import User as UserModel
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.base.user import User
from domain.values.hashed_password import HashedPasswordSHA256
from domain.values.Username import UserName


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
            is_active=model.is_active,
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
            "is_active": entity.is_active,
        }

        # Если у сущности задан ``id`` (str UUID), передаём его в модель,
        # иначе позволяем БД сгенерировать значение по умолчанию.
        if getattr(entity, "id", None):
            model_kwargs["id"] = UUID(str(entity.id))

        return UserModel(**model_kwargs)

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
        model = self._to_model(user)
        self._session.add(model)
        await self._session.flush()

        # Возвращаем новую доменную сущность, не изменяя исходную (frozen dataclass)
        return self._to_entity(model)

    async def update(self, user: User) -> User:
        """Обновляет пользователя.

        По факту вызывает :py:meth:`save`, так как сохранение покрывает
        сценарии обновления всех полей сущности.

        Args:
            user: Доменная сущность пользователя с изменёнными полями.

        Returns:
            Обновлённая доменная сущность пользователя.
        """
        # Возможно, этот метод не нужен, так как save обновляет все поля
        return await self.save(user)

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
        query = select(UserModel).where(UserModel.id == UUID(user_id))
        result = await self._session.execute(query)
        model = result.scalar_one_or_none()

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
