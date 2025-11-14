"""
Test Python syntax and code quality
"""

import pytest
import sys
import os
import ast
import py_compile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_python_files():
    """Get all Python files in backend directory"""
    backend_dir = Path(__file__).parent.parent
    python_files = list(backend_dir.glob("*.py"))
    return [f for f in python_files if f.name != "__pycache__"]


@pytest.mark.parametrize("python_file", get_python_files())
def test_python_syntax(python_file):
    """Test that all Python files have valid syntax"""
    try:
        with open(python_file, 'r') as f:
            code = f.read()
        ast.parse(code)
        assert True
    except SyntaxError as e:
        pytest.fail(f"Syntax error in {python_file}: {e}")


@pytest.mark.parametrize("python_file", get_python_files())
def test_python_compiles(python_file):
    """Test that all Python files compile"""
    try:
        py_compile.compile(str(python_file), doraise=True)
        assert True
    except py_compile.PyCompileError as e:
        pytest.fail(f"Compilation error in {python_file}: {e}")


def test_main_has_fastapi_app():
    """Test that main.py has FastAPI app"""
    from main import app
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)


def test_main_has_required_endpoints():
    """Test that main.py has required endpoints"""
    from main import app

    routes = [route.path for route in app.routes]

    # Check required endpoints exist
    assert "/" in routes
    assert "/api/health" in routes
    assert "/api/chat" in routes
    assert "/api/tts" in routes


def test_tts_engine_has_required_methods():
    """Test that TTS engine has required methods"""
    from tts_engine import TransformersTTSEngine

    engine = TransformersTTSEngine(force_cpu=True)

    # Check required methods exist
    assert hasattr(engine, 'load_model')
    assert hasattr(engine, 'synthesize')
    assert hasattr(engine, 'synthesize_streaming')
    assert hasattr(engine, 'get_supported_languages')
    assert hasattr(engine, 'is_ready')


def test_openai_client_has_required_methods():
    """Test that OpenAI client has required methods"""
    from openai_integration import OpenAIClient
    from unittest.mock import patch

    with patch("openai_integration.OpenAI"):
        with patch.object(OpenAIClient, '_test_connection'):
            client = OpenAIClient(api_key="test-key")

            # Check required methods exist
            assert hasattr(client, 'get_completion')
            assert hasattr(client, 'get_streaming_completion')
            assert hasattr(client, 'create_conversation_id')
            assert hasattr(client, 'clear_conversation')
            assert hasattr(client, 'get_conversation_history')


def test_no_print_statements():
    """Test that code uses logging instead of print"""
    for python_file in get_python_files():
        with open(python_file, 'r') as f:
            content = f.read()

        # Allow print in test files
        if 'test_' in python_file.name:
            continue

        # Check for print statements (basic check)
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Skip comments and strings
            if line.strip().startswith('#'):
                continue
            if 'print(' in line and 'logging' not in content:
                pytest.fail(f"Found print() in {python_file}:{i} - use logging instead")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
