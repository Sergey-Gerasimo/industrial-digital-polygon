## Руководство пользователя

Это краткое руководство поможет быстро запустить проект локально и выполнить базовые проверки.

### 1. Подготовка окружения

Установите зависимости для запуска в контейнерах:
- Docker
- Docker Compose
- Make

Создайте файл `.env` в корне проекта (при необходимости):

```env
# API
API_HOST=0.0.0.0
API_PORT=8080
API_RELOAD=true
API_ALLOWED_HOSTS=*

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=rabbitmq_user
RABBITMQ_PASSWORD=rabbitmq_password

# Security
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080
```

Значения можно оставить по умолчанию для локального старта, но не используйте их в production.

### 2. Запуск

```bash
make all        # поднять хранилища и приложение
# или
make storages   # отдельно поднять инфраструктуру (DB/Redis/RabbitMQ)
make app        # собрать и запустить приложение
```

Проверка статуса и логов:

```bash
make app-logs   # поток логов приложения
make app-shell  # интерактивная оболочка внутри контейнера
```

Остановка:

```bash
make app-down
make storages-down
```

### 3. Проверка работы API

Откройте в браузере `http://localhost:8080/api/docs` — вы увидите Swagger UI.

CLI-проверка:

```bash
curl -i http://localhost:8080/api/docs
```

### 4. Тестирование

```bash
make test
```

Тесты запускаются внутри контейнера приложения.

### 5. Типичные проблемы

- Порт занят: измените `API_PORT` в `.env` или освободите порт 8080.
- Переменные окружения не применяются: убедитесь, что команды запуска выполняются с `--env-file .env` (см. `Makefile`) и файл `.env` в корне.
- Медленный старт: первый запуск тянет базовые образы Docker и кэш зависимостей.

### 6. Что дальше?

- Изучите структуру `app/domain` и `app/logic` для понимания предметной области.
- Загляните в `docs/ARCHITECTURE.md` для обзора слоев и точек расширения.
- Проверьте `docs/API.md` для доступа к Swagger и стандартов API.


