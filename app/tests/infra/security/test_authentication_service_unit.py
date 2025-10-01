import pytest

from infra.security.authentication_service import PasswordAuthenticationService


@pytest.mark.fast
class TestPasswordAuthenticationService:
    def test_hash_password_returns_value_object(self):
        service = PasswordAuthenticationService()
        hashed = service.hash_password("StrongPass!42")

        assert hasattr(hashed, "value")
        assert isinstance(hashed.value, str)
        assert len(hashed.value) > 0

    def test_verify_password_success(self):
        service = PasswordAuthenticationService()
        plain = "StrongPass!42"
        hashed = service.hash_password(plain)

        assert service.verify_password(plain, hashed) is True

    def test_verify_password_failure(self):
        service = PasswordAuthenticationService()
        hashed = service.hash_password("StrongPass!42")

        assert service.verify_password("wrong", hashed) is False
