import pytest


def register_markers():
    """Функция для регистрации меток"""
    markers = {
        "slow": "Медленные тесты",
        "fast": "Быстрые тесты",
        "integration": "Интеграционные тесты",
        "infra": "Тесты инфраструктуры",
        "rabbitmq": "Тесты RabbitMQ",
        "database": "Тесты базы данных",
    }

    return markers


def pytest_configure(config):
    """Регистрация всех меток"""
    markers = register_markers()
    for marker, description in markers.items():
        config.addinivalue_line("markers", f"{marker}: {description}")
