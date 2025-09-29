"""
Пакет репозиториев доступа к данным.

Содержит абстракции и конкретные реализации репозиториев для работы с БД через
асинхронную сессию SQLAlchemy. Используйте конкретные реализации (например,
``UserRepository``) для доменных операций хранения и выборки.
"""

from infra.database.repositories.user_reposytory import UserRepository

__all__ = ["UserRepository"]
