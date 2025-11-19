"""
API tests for TTS endpoint (TDD - Tests written FIRST)

Tests text-to-speech synthesis endpoint.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI


class TestTTSEndpoint:
    """Tests for POST /api/v1/tts endpoint"""

    @pytest.mark.asyncio
    async def test_tts_returns_200(self, test_app: FastAPI, mock_tts_service):
        """Test that TTS endpoint returns 200 OK"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tts",
                json={"text": "Hello world"}
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_tts_requires_text(self, test_app: FastAPI):
        """Test that text field is required"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post("/api/v1/tts", json={})
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_tts_returns_audio_data(self, test_app: FastAPI, mock_tts_service):
        """Test that TTS returns audio as streaming response"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tts",
                json={"text": "Hello world"}
            )
            assert response.status_code == 200
            # Should return audio content type
            assert "audio" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_tts_calls_tts_service(self, test_app: FastAPI, mock_tts_service):
        """Test that TTS endpoint calls TTSService.synthesize"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            await client.post(
                "/api/v1/tts",
                json={"text": "Hello world"}
            )

            # Verify service was called
            mock_tts_service.synthesize.assert_called_once()
            call_args = mock_tts_service.synthesize.call_args
            assert call_args.kwargs["text"] == "Hello world"

    @pytest.mark.asyncio
    async def test_tts_with_language(self, test_app: FastAPI, mock_tts_service):
        """Test TTS with custom language"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            await client.post(
                "/api/v1/tts",
                json={"text": "Bonjour", "language": "fr"}
            )

            # Verify language was passed
            call_args = mock_tts_service.synthesize.call_args
            assert call_args.kwargs["language"] == "fr"

    @pytest.mark.asyncio
    async def test_tts_validates_text_not_empty(self, test_app: FastAPI):
        """Test that text must not be empty"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tts",
                json={"text": ""}
            )
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_tts_handles_service_error(self, test_app: FastAPI, mock_tts_service):
        """Test that TTS endpoint handles service errors gracefully"""
        # Mock service to raise an error
        mock_tts_service.synthesize.side_effect = Exception("TTS error")

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tts",
                json={"text": "Hello"}
            )
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_tts_handles_invalid_language(self, test_app: FastAPI, mock_tts_service):
        """Test that TTS handles invalid language gracefully"""
        # Mock service to raise ValueError for invalid language
        mock_tts_service.synthesize.side_effect = ValueError("Unsupported language")

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tts",
                json={"text": "Hello", "language": "invalid"}
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_tts_validates_text_length(self, test_app: FastAPI):
        """Test that text has reasonable length limits"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            # Very long text (> 5000 characters)
            long_text = "a" * 6000
            response = await client.post(
                "/api/v1/tts",
                json={"text": long_text}
            )
            # Should either succeed or return validation error, not crash
            assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_tts_returns_wav_format(self, test_app: FastAPI, mock_tts_service):
        """Test that TTS returns WAV audio format"""
        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/tts",
                json={"text": "Hello"}
            )

            # Check content type
            content_type = response.headers.get("content-type", "")
            assert "audio/wav" in content_type or "audio/wave" in content_type
