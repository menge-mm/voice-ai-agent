"""
Pytest configuration and shared fixtures
"""
import os
import pytest
from typing import Generator


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables before any tests run"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DEBUG"] = "true"

    # Set required environment variables for testing
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test_db")
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
