"""
Pytest configuration and shared fixtures
"""
import os
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text

# Import Base and all models at module level so they're registered
from app.db.base import Base
from app.db.models.user import User
from app.db.models.conversation import Conversation
from app.db.models.message import Message


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables before any tests run"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"

    # Set required environment variables for testing
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
    os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")

    yield

    # Cleanup after all tests
    os.environ.pop("ENVIRONMENT", None)
    os.environ.pop("DEBUG", None)


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture to provide a clean environment for testing"""
    # Store original env
    original_env = os.environ.copy()

    yield monkeypatch

    # Restore original env
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an async database session for testing.
    Uses in-memory SQLite for fast tests.

    Important: For SQLite :memory: databases, we must use a single connection
    throughout the test, otherwise each new connection gets a fresh empty database.
    """
    # Create in-memory SQLite database for testing
    # StaticPool ensures all connections use the same in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Provide session for test
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    # Cleanup
    await engine.dispose()
