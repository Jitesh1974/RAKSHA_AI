from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def database_url() -> str:
    value = os.getenv("DATABASE_URL", "").strip()
    if not value:
        raise RuntimeError("DATABASE_URL is not configured")
    if value.startswith("postgresql://"):
        value = value.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif value.startswith("postgres://"):
        value = value.replace("postgres://", "postgresql+asyncpg://", 1)
    return value


def _pool_kwargs() -> dict[str, int]:
    return {
        "pool_size": max(1, int(os.getenv("DB_POOL_SIZE", "10"))),
        "max_overflow": max(0, int(os.getenv("DB_MAX_OVERFLOW", "20"))),
    }


engine = create_async_engine(database_url(), pool_pre_ping=True, **_pool_kwargs())
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def check_database() -> bool:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
