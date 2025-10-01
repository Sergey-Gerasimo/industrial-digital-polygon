from uuid import uuid4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from .models import User, UserRole, Base
from infra.config import settings, app_logger
from domain.values import HashedPasswordSHA256


async def create_tables(async_engine: AsyncEngine) -> None:
    app_logger.info("Stargin database tables creation...")

    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            app_logger.info("Database tables created successfully")

    except Exception as e:
        app_logger.error(f"Failed to create database tables: {e}")
        raise


async def drop_tables(async_engine: AsyncEngine) -> None:
    app_logger.warning("Starting database tables drop...")

    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            app_logger.warning("Database tables dropped successfully")

    except Exception as e:
        app_logger.error(f"Failed to drop database tables: {e}")


async def create_super_user(
    async_engine: AsyncEngine, username: str, password: str
) -> User:

    async with async_engine.begin() as conn:

        check_result = await conn.execute(
            text("SELECT 1 FROM users WHERE username = :username"),
            {"username": username},
        )
        existing_user = check_result.scalar_one_or_none()

        if existing_user:
            app_logger.info(f"Superuser '{username}' already exists")
            return

        user_id = uuid4()
        hashed_password = HashedPasswordSHA256.from_plain_password(password).value

        await conn.execute(
            text(
                """
                INSERT INTO users (id, username, hashed_password, role, is_active, created_at, updated_at)
                VALUES (:id, :username, :hashed_password, :role, :is_active, NOW(), NOW())
            """
            ),
            {
                "id": user_id,
                "username": username,
                "hashed_password": hashed_password,
                "role": "ADMIN",
                "is_active": True,
            },
        )
        await conn.commit()

        app_logger.info(
            f"Superuser '{username}' created successfully with ID: {user_id}"
        )
