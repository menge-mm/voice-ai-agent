"""
Test OpenAI Integration
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai_integration import OpenAIClient


def test_openai_client_requires_api_key():
    """Test that OpenAI client requires API key"""
    # Clear environment variable
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OpenAI API key not found"):
            OpenAIClient()


def test_openai_client_initialization_with_key():
    """Test OpenAI client initialization with API key"""
    with patch("openai_integration.OpenAI") as mock_openai:
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key")
            assert client.api_key == "sk-test-key"
            assert client.model == "gpt-4-turbo"


def test_openai_client_custom_model():
    """Test OpenAI client with custom model"""
    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key", model="gpt-3.5-turbo")
            assert client.model == "gpt-3.5-turbo"


def test_openai_create_conversation_id():
    """Test conversation ID creation"""
    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key")
            conv_id = client.create_conversation_id()
            assert isinstance(conv_id, str)
            assert len(conv_id) > 0


def test_openai_is_connected():
    """Test is_connected method"""
    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key")
            assert client.is_connected()


def test_openai_estimate_tokens():
    """Test token estimation"""
    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key")
            tokens = client.estimate_tokens("Hello world")
            assert isinstance(tokens, int)
            assert tokens > 0


def test_openai_set_model():
    """Test setting model"""
    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key")
            client.set_model("gpt-3.5-turbo")
            assert client.model == "gpt-3.5-turbo"


def test_openai_clear_conversation():
    """Test clearing conversation"""
    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key")
            conv_id = "test-id"
            client.conversations[conv_id] = [{"role": "user", "content": "test"}]
            client.clear_conversation(conv_id)
            assert conv_id not in client.conversations


def test_openai_get_conversation_history():
    """Test getting conversation history"""
    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key")
            conv_id = "test-id"
            test_history = [{"role": "user", "content": "test"}]
            client.conversations[conv_id] = test_history
            history = client.get_conversation_history(conv_id)
            assert history == test_history


def test_openai_get_conversation_summary():
    """Test getting conversation summary"""
    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="sk-test-key")
            conv_id = "test-id"
            client.conversations[conv_id] = [
                {"role": "user", "content": "hi", "timestamp": "2025-01-01T00:00:00"},
                {"role": "assistant", "content": "hello", "timestamp": "2025-01-01T00:00:01"}
            ]
            summary = client.get_conversation_summary(conv_id)
            assert summary["conversation_id"] == conv_id
            assert summary["message_count"] == 2
            assert summary["exchanges"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
