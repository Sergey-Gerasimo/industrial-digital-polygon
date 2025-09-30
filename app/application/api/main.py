from contextlib import asynccontextmanager
from fastapi import FastAPI


from infra.config import settings
from infra.database import async_engine
from infra.database.utils import create_super_user, create_tables, drop_tables
from application.api.routes.auth import router as auth_router
from application.api.routes.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения.

    """
    await create_tables(async_engine)
    await create_super_user(
        async_engine=async_engine,
        username=settings.superuser.username,
        password=settings.superuser.password,
    )
    yield
    await drop_tables(async_engine)


def create_app():
    app = FastAPI(
        title="Industrial-Digital-Polygon",
        docs_url="/api/docs",
        description="Цифровой полигон: где станки общаются JSON'ом, а сменный мастер требует 'сделать красиво'",
        lifespan=lifespan,
    )
    app.include_router(router=auth_router)
    app.include_router(router=users_router)

    return app
