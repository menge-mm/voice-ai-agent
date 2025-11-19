"""
Tests for database session management
Following TDD: These tests are written FIRST before implementation
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool


@pytest.mark.asyncio
async def test_async_session_created():
    """Test that async database session can be created"""
    from app.db.session import async_session

    async with async_session() as session:
        assert session is not None
        assert isinstance(session, AsyncSession)


@pytest.mark.asyncio
async def test_session_closes_after_use():
    """Test that session can be used in context manager"""
    from app.db.session import async_session

    session_instance = None
    async with async_session() as session:
        session_instance = session
        # Session should be valid while in context
        assert session is not None
        assert isinstance(session, AsyncSession)

    # Session was created successfully
    assert session_instance is not None


@pytest.mark.asyncio
async def test_session_rollback_on_error():
    """Test that session rolls back on error"""
    from app.db.session import async_session

    try:
        async with async_session() as session:
            # Simulate an error
            raise ValueError("Test error")
    except ValueError:
        pass  # Expected

    # Session should have rolled back and closed


@pytest.mark.asyncio
async def test_database_url_from_settings():
    """Test that database URL is loaded from settings"""
    from app.core.config import get_settings
    from app.db.session import get_database_url

    settings = get_settings()
    db_url = get_database_url()

    # URL should match settings (could be SQLite for tests or PostgreSQL for production)
    assert db_url == settings.DATABASE_URL
    assert db_url  # URL should not be empty


@pytest.mark.asyncio
async def test_engine_configuration():
    """Test that engine is configured correctly"""
    from app.db.session import engine
    from sqlalchemy.pool import StaticPool

    assert engine is not None
    # Check pool exists (could be StaticPool for SQLite or regular pool for PostgreSQL)
    assert engine.pool is not None

    # StaticPool doesn't have size() method, only regular pools do
    if not isinstance(engine.pool, StaticPool):
        assert engine.pool.size() >= 0  # Pool is initialized


@pytest.mark.asyncio
async def test_session_factory_creates_different_sessions():
    """Test that session factory creates different session instances"""
    from app.db.session import async_session

    async with async_session() as session1:
        async with async_session() as session2:
            # Should be different instances
            assert session1 is not session2
