from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from infra.config import app_logger as logger


class AuthMiddleware:
    """
    Middleware для дополнительной аутентификации и авторизации
    """

    @staticmethod
    async def process_request(request: Request, call_next):
        """
        Базовая проверка аутентификации для защищенных эндпоинтов
        """
        # Пропускаем публичные эндпоинты
        public_paths = [
            "/api/docs",
            "/api/redoc",
            "/health",
            "/api/auth/login",
            "/api/auth/register",
        ]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)

        # Проверяем наличие Authorization header для защищенных путей
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(
                "MISSING_AUTH_HEADER",
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"},
            )

        # Дополнительные проверки могут быть добавлены здесь
        return await call_next(request)


# Функция-обертка для использования в FastAPI
async def auth_middleware(request: Request, call_next):
    return await AuthMiddleware.process_request(request, call_next)
