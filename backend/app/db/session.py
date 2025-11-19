"""
Database session management with async SQLAlchemy
"""
from typing import AsyncGenerator
from functools import lru_cache
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


def get_database_url() -> str:
    """Get database URL from settings"""
    settings = get_settings()
    return settings.DATABASE_URL


@lru_cache()
def get_engine() -> AsyncEngine:
    """
    Get cached async engine instance.
    Uses lru_cache to ensure only one engine is created.
    """
    settings = get_settings()

    # Configure engine based on database type
    # SQLite doesn't support pool_size/max_overflow parameters
    engine_kwargs = {
        "echo": settings.DB_ECHO,
    }

    # Add pooling options only for non-SQLite databases
    if "sqlite" not in settings.DATABASE_URL:
        engine_kwargs.update({
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_pre_ping": True,  # Verify connections before using
            "pool_recycle": 3600,  # Recycle connections after 1 hour
        })

    return create_async_engine(
        settings.DATABASE_URL,
        **engine_kwargs
    )


@lru_cache()
def get_async_session():
    """
    Get cached async session factory.
    Uses lru_cache to ensure only one factory is created.
    """
    return async_sessionmaker(
        get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


# Create engine and session factory using cached functions
# These will be created on first import, but can be cleared via cache_clear()
engine = get_engine()
async_session = get_async_session()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    Use this with FastAPI Depends.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    session_factory = get_async_session()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
