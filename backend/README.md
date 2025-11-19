# Voice AI Agent - Backend

Production-ready FastAPI backend with clean architecture following TDD principles.

## Features

- 🎯 **Clean Architecture**: Repository pattern, Service layer, Dependency injection
- 🧪 **Test-Driven Development**: 80%+ test coverage
- ⚡ **Async/Await**: Non-blocking database operations with SQLAlchemy 2.0
- 🗄️ **PostgreSQL**: Robust data persistence with Alembic migrations
- 🔄 **Redis**: Caching and rate limiting
- 🤖 **OpenAI Integration**: GPT-4 powered conversations
- 🔊 **TTS Support**: HuggingFace Transformers (SpeechT5, Bark)
- 📊 **Monitoring**: Prometheus metrics, Grafana dashboards, Sentry error tracking
- 🔒 **Security**: JWT authentication, rate limiting, input validation

## Tech Stack

- **Framework**: FastAPI 0.116.1 + Uvicorn
- **Database**: PostgreSQL 16 + SQLAlchemy 2.0 (async) + Alembic
- **Cache**: Redis 7 + aiocache
- **AI/ML**: OpenAI, HuggingFace Transformers, PyTorch 2.5
- **Audio**: librosa, soundfile, speechbrain
- **Testing**: pytest + pytest-asyncio + pytest-cov
- **Code Quality**: ruff, black, mypy, pre-commit

## Installation

```bash
# Install dependencies with Poetry
poetry install

# Or with pip
pip install -r requirements.txt
```

## Running

```bash
# Development server with hot reload
poetry run uvicorn app.main:app --reload

# Production server
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_repositories.py -v
```

## Database Migrations

```bash
# Create migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API endpoints
│   ├── core/                # Configuration
│   ├── db/                  # Database models
│   ├── models/              # Pydantic schemas
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic
│   ├── cache/               # Caching layer
│   ├── middleware/          # Custom middleware
│   └── utils/               # Utilities
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── alembic/                 # Database migrations
└── docker/                  # Docker configuration
```

## Docker

```bash
# Start all services (PostgreSQL, Redis, Prometheus, Grafana)
cd docker
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

## Development

- **Code Style**: Black (formatting), Ruff (linting)
- **Type Checking**: mypy
- **Pre-commit Hooks**: Configured for all quality checks
- **Test Coverage Target**: > 80%

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## Status

**Current Progress**:
- ✅ Day 1-2: Project setup, configuration, database models
- ✅ Day 3: Repository layer (CRUD operations)
- 🚧 Day 4: Service layer (OpenAI, TTS, Chat)
- ⏳ Day 5: Cache & dependency injection
- ⏳ Day 6: API endpoints
- ⏳ Day 7: Middleware & testing

## License

MIT
