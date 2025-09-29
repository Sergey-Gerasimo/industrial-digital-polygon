## Индустриальный цифровой полигон — документация

Добро пожаловать в документацию проекта «Индустриальный цифровой полигон». Здесь собраны материалы для быстрого старта, настройки окружения и понимания архитектуры.

- Быстрый старт: команды запуска и тестирования
- Конфигурация: переменные окружения и настройки
- Архитектура: слои приложения и ключевые модули
- API: базовые сведения и ссылки на Swagger
- Руководство пользователя: сценарии использования

См. также:
- [Архитектура](./ARCHITECTURE.md)
- [API](./API.md)
- [Руководство пользователя](./user_guide/index.md)

### Быстрый старт

Требования: установлены `docker`, `docker compose` и `make`.

```bash
make            # поднять инфраструктуру по умолчанию
make app        # собрать и запустить приложение (фоново)
make app-down   # остановить приложение
make app-logs   # поток логов приложения
make test       # запуск тестов внутри контейнера
make app-shell  # оболочка внутри контейнера приложения
```

После запуска приложение доступно по адресу `http://localhost:8080`, Swagger UI — по `http://localhost:8080/api/docs`.

### Конфигурация окружения

Все настройки читаются из переменных окружения (см. `app/infra/config/settings.py`). Рекомендуется использовать файл `.env` в корне проекта. Ключевые параметры:

- API: `API_HOST`, `API_PORT`, `API_RELOAD`, `API_ALLOWED_HOSTS`
- БД (PostgreSQL): `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_POOL_SIZE`, `POSTGRES_MAX_OVERFLOW`, `POSTGRES_ECHO`
- Redis: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`, `REDIS_MAX_CONNECTIONS`, `REDIS_DECODE_RESPONSES`, `REDIS_DEFAULT_TIMEOUT`
- RabbitMQ: `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_TIMEOUT`, `RABBITMQ_MAX_CONNECTIONS`, `RABBITMQ_RABBITMQ_MANAGEMENT_PORT`, `RABBITMQ_DEFAULT_QUEUE`
- Безопасность: `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`
- Прочее: `PYTHONPATH`

При запуске с дефолтами приложение выводит предупреждения о небезопасных значениях — замените их в `.env` для production.

### Зависимости

Управляются Poetry (см. `pyproject.toml`). В контейнерах ставятся автоматически. Локально установка не требуется для быстрого старта через Docker.


