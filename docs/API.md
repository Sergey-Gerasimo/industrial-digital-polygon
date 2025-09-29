## API

Приложение поднимает FastAPI со Swagger UI по адресу `/api/docs`.

Базовый URL локально: `http://localhost:8080`

### Документация Swagger

- Swagger UI: `GET /api/docs`
- OpenAPI JSON: `GET /openapi.json`

На текущем этапе эндпоинты могут отсутствовать или быть в разработке. Используйте Swagger для актуального списка маршрутов.

### Пример проверки доступности

```bash
curl -i http://localhost:8080/api/docs
```

Ожидается ответ `200 OK` и HTML Swagger UI.

### Стандарты

- Ответы в формате JSON.
- Аутентификация (при появлении защищенных эндпоинтов): JWT (см. `infra/security`).
- Логирование запросов — настраивается через переменные окружения (см. `config/settings.py`).


