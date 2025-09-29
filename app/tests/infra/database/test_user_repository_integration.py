import pytest
from uuid import UUID

from infra.database.repositories.user_reposytory import UserRepository
from domain.entities.base.user import User
from domain.values.Username import UserName
from domain.values.hashed_password import HashedPasswordSHA256


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.asyncio
class TestUserRepositoryIntegration:
    async def test_get_by_id(self, async_session):
        repo = UserRepository(async_session)
        entity = User(
            id="",
            username=UserName("getbyid"),
            password_hash=HashedPasswordSHA256("f" * 64),
            is_active=True,
        )

        saved = await repo.save(entity)
        fetched = await repo.get_by_id(saved.id)

        assert fetched is not None
        assert fetched.id == saved.id
        assert fetched.username.value == "getbyid"
        assert fetched.is_active is True

    async def test_save_and_get_by_username(self, async_session):
        repo = UserRepository(async_session)
        entity = User(
            id="",
            username=UserName("charlie"),
            password_hash=HashedPasswordSHA256("c" * 64),
            is_active=True,
        )

        saved = await repo.save(entity)
        assert saved.id
        UUID(saved.id)

        fetched = await repo.get_by_username(UserName("charlie"))
        assert fetched is not None
        assert fetched.username.value == "charlie"

    async def test_delete(self, async_session):
        repo = UserRepository(async_session)
        entity = User(
            id="",
            username=UserName("dana"),
            password_hash=HashedPasswordSHA256("d" * 64),
            is_active=True,
        )
        saved = await repo.save(entity)

        ok = await repo.delete(saved.id)
        assert ok is True

        none_user = await repo.get_by_id(saved.id)
        assert none_user is None

    async def test_exists_with_username(self, async_session):
        repo = UserRepository(async_session)
        entity = User(
            id="",
            username=UserName("erin"),
            password_hash=HashedPasswordSHA256("e" * 64),
            is_active=False,
        )
        await repo.save(entity)

        assert await repo.exists_with_username(UserName("erin")) is True
        assert await repo.exists_with_username(UserName("ghost")) is False
