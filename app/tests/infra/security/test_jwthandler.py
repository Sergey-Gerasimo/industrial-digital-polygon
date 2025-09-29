import datetime
import time
import pytest
from jose import jwt
from infra.config import settings


@pytest.mark.infra
class TestJWTHandler:
    def test_create_access_token(self, jwt_handler, valid_subject):
        """Тестируем создание доступного токена"""
        token = jwt_handler.create_access_token(valid_subject)
        assert isinstance(token, str)
        decoded_payload = jwt.decode(
            token, jwt_handler.secret_key, algorithms=[jwt_handler.algorithm]
        )
        assert decoded_payload["sub"] == valid_subject

    def test_verify_valid_token(self, jwt_handler, valid_subject):
        """Проверяем работу метода verify_token с правильным токеном"""
        token = jwt_handler.create_access_token(valid_subject)
        verified_payload = jwt_handler.verify_token(token)
        assert verified_payload is not None
        assert verified_payload["sub"] == valid_subject

    def test_verify_invalid_token(self, jwt_handler, invalid_token):
        """Проверяем обработку некорректного токена"""
        verified_payload = jwt_handler.verify_token(invalid_token)
        assert verified_payload is None

    def test_verify_expired_token(self, jwt_handler, expired_token):
        """Проверяем реакцию на истечение срока токена"""
        verified_payload = jwt_handler.verify_token(expired_token)
        assert verified_payload is None

    def test_custom_expires_delta(self, jwt_handler, valid_subject):
        """Проверяем работу с кастомным сроком жизни токена"""
        # Используем datetime.timedelta напрямую
        delta = 5
        token = jwt_handler.create_access_token(valid_subject, expires_delta=delta)
        assert isinstance(token, str)

        decoded_payload = jwt.decode(
            token, jwt_handler.secret_key, algorithms=[jwt_handler.algorithm]
        )

        # Более надежная проверка времени expiration
        expected_exp = datetime.datetime.now().timestamp() + (delta * 60)
        actual_exp = decoded_payload["exp"]
        # Допускаем расхождение в 2 секунды из-за времени выполнения
        assert abs(actual_exp - expected_exp) <= 2

    def test_refresh_token_creation(self, jwt_handler, valid_subject):
        """Проверяем создание refresh-токена"""
        token = jwt_handler.create_refresh_token(valid_subject)
        assert isinstance(token, str)
        decoded_payload = jwt.decode(
            token, jwt_handler.secret_key, algorithms=[jwt_handler.algorithm]
        )
        assert decoded_payload["sub"] == valid_subject

    def test_expiration_with_delay(self, jwt_handler, valid_subject):
        """Проверяем фактическое истечение срока токена"""
        # Создаем токен с очень коротким временем жизни для теста
        short_lived_token = jwt_handler.create_access_token(
            valid_subject, expires_delta=2 / 60
        )

        # Проверяем, что токен валиден сразу после создания
        verified_payload = jwt_handler.verify_token(short_lived_token)
        assert verified_payload is not None

        # Ждем истечения срока
        time.sleep(3)

        # Проверяем, что токен теперь невалиден
        verified_payload = jwt_handler.verify_token(short_lived_token)
        assert verified_payload is None
