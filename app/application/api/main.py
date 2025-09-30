from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from infra.config.log_settings import app_logger
from infra.config import settings
from infra.database import async_engine
from infra.database.utils import create_super_user, create_tables, drop_tables
from application.api.routes.auth import router as auth_router
from application.api.routes.users import router as users_router
from application.api.middleware import logging_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения.

    """
    app_logger.info("Starting Industrial Digital Polygon API")

    try:
        await create_tables(async_engine)
        app_logger.info("Database tables created successfully")

        await create_super_user(
            async_engine=async_engine,
            username=settings.superuser.username,
            password=settings.superuser.password,
        )

        app_logger.info("Superuser check completed")

    except Exception as e:
        app_logger.error(f"Application startup failed: {str(e)}")
        raise

    app_logger.info("Application startup completed successfully")

    yield
    app_logger.info("Shutting down application...")

    try:
        await drop_tables(async_engine)
        app_logger.info("Database tables dropped successfully")
    except Exception as e:
        app_logger.error(f"Application shutdown error: {str(e)}")


def create_app():

    app = FastAPI(
        title="Industrial-Digital-Polygon",
        docs_url="/api/docs",
        description="Цифровой полигон: где станки общаются JSON'ом, а сменный мастер требует 'сделать красиво'",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.middleware("http")(logging_middleware)

    app.include_router(router=auth_router)
    app.include_router(router=users_router)

    return app
