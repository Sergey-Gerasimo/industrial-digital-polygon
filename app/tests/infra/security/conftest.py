import pytest
import datetime
from jose import jwt

from infra.security import JWTHandler
from infra.config import settings


@pytest.fixture(scope="module")
def jwt_handler():
    """Фикстура для создания экземпляра JWTHandler."""
    return JWTHandler(
        access_token_expire_minutes=settings.secrurity.access_token_expire_minutes,
        refresh_token_expire_minutes=settings.secrurity.refresh_token_expire_minutes,
        secret_key=settings.secrurity.secret_key,
        algorithm=settings.secrurity.algorithm,
    )


@pytest.fixture(scope="module")
def valid_subject():
    """Идентификатор пользователя для теста."""
    return "test_user"


@pytest.fixture(scope="module")
def invalid_token():
    """Некорректный токен для проверки исключительных ситуаций."""
    return "invalid.token.string"


@pytest.fixture(scope="module")
def expired_token(jwt_handler, valid_subject):
    """Создаем токен, срок которого заведомо истек."""
    past_time = datetime.datetime.now() - datetime.timedelta(hours=1)
    to_encode = {"exp": past_time.timestamp(), "sub": valid_subject}
    return jwt.encode(to_encode, jwt_handler.secret_key, jwt_handler.algorithm)
