"""
Базовые абстракции для репозиториев.

Предоставляет обобщённый абстрактный класс репозитория, инкапсулирующий доступ к
асинхронной сессии SQLAlchemy и преобразования между доменными сущностями и
моделями БД.

Пример:
    Определение конкретного репозитория::

        from sqlalchemy.ext.asyncio import AsyncSession
        from infra.database.repositories.base import BaseRepository

        class MyEntity: ...
        class MyModel: ...

        class MyRepository(BaseRepository[MyEntity, MyModel]):
            def __init__(self, session: AsyncSession):
                super().__init__(session)

            def _to_entity(self, model: MyModel) -> MyEntity:
                return MyEntity()

            def _to_model(self, entity: MyEntity) -> MyModel:
                return MyModel()
"""

from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Optional

TEntity = TypeVar("TEntity")
TModel = TypeVar("TModel")


class BaseRepository(Generic[TEntity, TModel], ABC):
    """Абстрактный базовый класс для репозиториев.

    Содержит ссылку на асинхронную сессию SQLAlchemy и определяет контракт
    преобразования между моделью БД и доменной сущностью.

    Args:
        session: Экземпляр ``AsyncSession`` для выполнения запросов к БД.
    """

    def __init__(self, session: AsyncSession):
        """Инициализирует репозиторий.

        Args:
            session: Асинхронная сессия SQLAlchemy.
        """
        self._session = session

    @abstractmethod
    def _to_entity(self, model: TModel) -> TEntity:
        """Преобразует модель БД в доменную сущность.

        Args:
            model: Объект модели уровня БД.

        Returns:
            Доменная сущность.
        """
        pass

    @abstractmethod
    def _to_model(self, entity: TEntity) -> TModel:
        """Преобразует доменную сущность в модель БД.

        Args:
            entity: Доменная сущность.

        Returns:
            Объект модели уровня БД.
        """
        pass
