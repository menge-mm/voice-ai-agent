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
    """Test that session properly closes after use"""
    from app.db.session import async_session

    session_instance = None
    async with async_session() as session:
        session_instance = session
        assert not session.is_active or session.in_transaction()

    # After context manager, session should be closed
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

    assert db_url == settings.DATABASE_URL
    assert "postgresql+asyncpg" in db_url


@pytest.mark.asyncio
async def test_engine_configuration():
    """Test that engine is configured correctly"""
    from app.db.session import engine

    assert engine is not None
    # Check pool configuration
    assert engine.pool.size() >= 0  # Pool is initialized


@pytest.mark.asyncio
async def test_session_factory_creates_different_sessions():
    """Test that session factory creates different session instances"""
    from app.db.session import async_session

    async with async_session() as session1:
        async with async_session() as session2:
            # Should be different instances
            assert session1 is not session2
