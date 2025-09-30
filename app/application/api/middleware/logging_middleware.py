import time
from fastapi import Request
from uuid import uuid4

from infra.config import app_logger as logger


async def logging_middleware(request: Request, call_next):
    """
    Middleware для логирования всех HTTP запросов
    """
    request_id = str(uuid4())
    request.state.request_id = request_id

    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")[
        :200
    ]  # Ограничиваем длину

    # Логируем начало запроса
    logger.info(
        "HTTP_REQUEST_START",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
        client_ip=client_ip,
        user_agent=user_agent,
        path=request.url.path,
    )

    try:
        response = await call_next(request)
        duration = round((time.time() - start_time) * 1000, 2)

        # Логируем успешное завершение
        logger.info(
            "HTTP_REQUEST_COMPLETE",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration,
            client_ip=client_ip,
        )

        return response

    except Exception as exc:
        duration = round((time.time() - start_time) * 1000, 2)

        logger.error(
            "HTTP_REQUEST_ERROR",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            error_type=type(exc).__name__,
            error_message=str(exc),
            duration_ms=duration,
            client_ip=client_ip,
            stack_trace=True,
        )
        raise


class LoggingMiddleware:
    """Классовая версия middleware для логирования"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope, receive)
        await logging_middleware(request, lambda: self.app(scope, receive, send))
