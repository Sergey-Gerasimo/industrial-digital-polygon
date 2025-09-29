import pytest
from uuid import UUID, uuid4

from infra.database.repositories.user_reposytory import UserRepository
from infra.database.models import User as UserModel
from domain.entities.base.user import User
from domain.values.Username import UserName
from domain.values.hashed_password import HashedPasswordSHA256


@pytest.mark.fast
class TestUserRepositoryUnit:
    def test_to_model_converts_domain_to_db_model(self):
        repo = UserRepository.__new__(UserRepository)
        repo._session = None  # type: ignore[assignment]

        entity = User(
            id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            username=UserName("alice"),
            password_hash=HashedPasswordSHA256("a" * 64),
            is_active=True,
        )

        model: UserModel = repo._to_model(entity)

        assert isinstance(model, UserModel)
        assert model.username == "alice"
        assert model.hashed_password == "a" * 64
        assert model.is_active is True
        assert isinstance(model.id, UUID)

    def test_to_entity_converts_db_model_to_domain(self):
        repo = UserRepository.__new__(UserRepository)
        repo._session = None  # type: ignore[assignment]

        model = UserModel(
            username="bob",
            hashed_password="b" * 64,
            is_active=False,
        )

        model.id = uuid4()

        entity = repo._to_entity(model)

        assert isinstance(entity, User)
        assert entity.username.value == "bob"
        assert entity.password_hash.value == "b" * 64
        assert entity.is_active is False
        UUID(entity.id)
