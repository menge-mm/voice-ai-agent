"""
Test that project structure is set up correctly
"""
import os
from pathlib import Path


def test_app_directory_exists():
    """Test that app directory exists"""
    app_dir = Path(__file__).parent.parent / "app"
    assert app_dir.exists()
    assert app_dir.is_dir()


def test_required_subdirectories_exist():
    """Test that all required subdirectories exist"""
    base_dir = Path(__file__).parent.parent / "app"
    required_dirs = [
        "api/v1/endpoints",
        "core",
        "db/models",
        "services",
        "repositories",
        "cache",
        "middleware",
        "utils",
        "workers",
    ]

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        assert full_path.exists(), f"Directory {dir_path} does not exist"
        assert full_path.is_dir(), f"{dir_path} is not a directory"


def test_all_packages_have_init_files():
    """Test that all directories have __init__.py files"""
    app_dir = Path(__file__).parent.parent / "app"

    for root, dirs, files in os.walk(app_dir):
        # Skip __pycache__ directories
        if "__pycache__" in root:
            continue

        root_path = Path(root)
        init_file = root_path / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py in {root_path}"


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists"""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject.exists()
    assert pyproject.is_file()


def test_precommit_config_exists():
    """Test that .pre-commit-config.yaml exists"""
    precommit = Path(__file__).parent.parent / ".pre-commit-config.yaml"
    assert precommit.exists()
    assert precommit.is_file()


def test_imports_work():
    """Test that basic imports work"""
    # This will fail if the structure is not correct
    try:
        import app
        import app.core
        import app.api
        import app.services
        import app.repositories
        import app.db
        import app.db.models
        import app.cache
        import app.middleware
        assert True
    except ImportError as e:
        assert False, f"Import failed: {e}"
