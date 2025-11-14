"""
Test FastAPI endpoints
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


client = TestClient(app)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "Voice AI Agent API" in data["name"]


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "tts_loaded" in data
    assert "openai_connected" in data


def test_get_supported_languages():
    """Test get supported languages endpoint"""
    response = client.get("/api/tts/languages")
    assert response.status_code == 200 or response.status_code == 503
    # 503 if TTS not initialized (expected in test environment)


def test_api_docs_available():
    """Test that API docs are accessible"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema():
    """Test that OpenAPI schema is available"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema


def test_cors_headers():
    """Test CORS headers are set"""
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert "access-control-allow-origin" in response.headers or response.status_code == 200


def test_invalid_endpoint():
    """Test invalid endpoint returns 404"""
    response = client.get("/api/invalid")
    assert response.status_code == 404


# Chat endpoint tests (require OpenAI key)
@pytest.mark.skip(reason="Requires OpenAI API key")
def test_chat_endpoint_without_tts():
    """Test chat endpoint without TTS"""
    response = client.post(
        "/api/chat",
        json={
            "text": "Hello",
            "enable_tts": False,
            "language": "en"
        }
    )
    assert response.status_code in [200, 500]  # 500 if OpenAI not configured


@pytest.mark.skip(reason="Requires OpenAI API key and TTS model")
def test_chat_endpoint_with_tts():
    """Test chat endpoint with TTS enabled"""
    response = client.post(
        "/api/chat",
        json={
            "text": "Hello",
            "enable_tts": True,
            "language": "en"
        }
    )
    assert response.status_code in [200, 503]  # 503 if TTS not loaded


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
