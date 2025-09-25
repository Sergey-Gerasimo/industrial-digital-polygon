from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.infra.config import settings as app_settings

async_engine = create_async_engine(
    app_settings.postgres.url_asyncpg,
    echo=True if app_settings.log.debug else False,
    pool_size=app_settings.postgres.pool_size,
    max_overflow=app_settings.postgres.max_overflow,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    repr_cols_num = 3
    repr_cols = tuple()

    def __repr__(self):
        """Relationships не используются в repr(), т.к. могут вести к неожиданным подгрузкам"""
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"


async def create_tables(async_engine: AsyncEngine) -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
