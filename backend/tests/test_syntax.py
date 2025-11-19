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
    """Test that app.main has FastAPI app"""
    from app.main import app
    from fastapi import FastAPI
    assert isinstance(app, FastAPI)


def test_main_has_required_endpoints():
    """Test that app.main has required endpoints"""
    from app.main import app

    routes = [route.path for route in app.routes]

    # Check required endpoints exist
    assert "/" in routes
    # Note: Clean architecture uses /health instead of /api/health
    assert any("/health" in r for r in routes)
    assert any("/chat" in r for r in routes)
    assert any("/tts" in r for r in routes)


def test_tts_engine_has_required_methods():
    """Test that TTS service has required methods"""
    from app.services.tts_service import TTSService

    # TTSService is the new implementation
    # Check required methods exist
    assert hasattr(TTSService, 'synthesize')
    assert hasattr(TTSService, 'get_supported_languages')


def test_openai_client_has_required_methods():
    """Test that OpenAI service has required methods"""
    from app.services.openai_service import OpenAIService

    # OpenAIService is the new implementation
    # Check required methods exist
    assert hasattr(OpenAIService, 'get_completion')
    assert hasattr(OpenAIService, 'get_completion_with_tokens')


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
