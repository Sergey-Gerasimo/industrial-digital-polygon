from contextlib import asynccontextmanager
from fastapi import FastAPI


from infra.database import async_engine, create_tables, drop_tables
from application.api.routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл приложения.

    """
    await create_tables(async_engine)
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

    return app
