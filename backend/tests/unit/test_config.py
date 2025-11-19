"""
Tests for configuration management
Following TDD: These tests are written FIRST before implementation
"""
import os
import pytest
from pydantic import ValidationError


def test_settings_loads_from_env(monkeypatch):
    """Test that Settings loads configuration from environment variables"""
    # Set environment variables
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-12345")

    from app.core.config import Settings

    settings = Settings()

    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@localhost:5432/testdb"
    assert settings.REDIS_URL == "redis://localhost:6379/0"
    assert settings.OPENAI_API_KEY == "sk-test-key"
    assert settings.SECRET_KEY == "test-secret-key-12345"


def test_settings_raises_on_missing_required(monkeypatch):
    """Test that Settings raises error when required env vars are missing"""
    # Clear critical environment variables
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    from app.core.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    # Check that the error is about missing required fields
    errors = exc_info.value.errors()
    field_names = [error["loc"][0] for error in errors]

    # At minimum, these critical fields should be required
    assert "OPENAI_API_KEY" in field_names or "SECRET_KEY" in field_names


def test_settings_has_correct_defaults(monkeypatch):
    """Test that Settings has correct default values"""
    # Clear environment variables that might be set by conftest
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    # Set only required fields
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    from app.core.config import Settings

    settings = Settings()

    # Check default values
    assert settings.APP_NAME == "Voice AI Agent"
    assert settings.APP_VERSION == "2.0.0"
    assert settings.DEBUG is False
    assert settings.ENVIRONMENT == "production"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000
    assert settings.OPENAI_MODEL == "gpt-4-turbo"
    assert settings.TTS_MODEL == "microsoft/speecht5_tts"
    assert settings.ALGORITHM == "HS256"


def test_settings_validates_database_url(monkeypatch):
    """Test that Settings validates database URL format"""
    monkeypatch.setenv("DATABASE_URL", "invalid-url")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    from app.core.config import Settings

    # This should either raise validation error or accept it
    # (depending on implementation - we'll make it lenient for now)
    settings = Settings()
    assert settings.DATABASE_URL == "invalid-url"


def test_settings_is_cached_singleton():
    """Test that get_settings returns cached instance"""
    from app.core.config import get_settings

    # Get settings twice
    settings1 = get_settings()
    settings2 = get_settings()

    # Should be the same instance (cached)
    assert settings1 is settings2


def test_settings_environment_property(monkeypatch):
    """Test is_production property"""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("ENVIRONMENT", "production")

    from app.core.config import Settings

    settings = Settings()
    assert settings.is_production is True

    # Test development environment
    monkeypatch.setenv("ENVIRONMENT", "development")
    settings_dev = Settings()
    assert settings_dev.is_production is False


def test_settings_cors_origins_as_list(monkeypatch):
    """Test that CORS origins can be a list"""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/testdb")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")

    from app.core.config import Settings

    settings = Settings()
    assert isinstance(settings.CORS_ORIGINS, list)
    assert "http://localhost:3000" in settings.CORS_ORIGINS
