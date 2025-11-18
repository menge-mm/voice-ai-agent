# Docker Setup for Voice AI Agent

## Services

This Docker Compose setup includes:

- **PostgreSQL 16**: Main database for storing conversations, users, and messages
- **Redis 7**: Caching layer for API responses and rate limiting
- **Backend API**: FastAPI application (development mode with hot reload)
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## Quick Start

### 1. Set up environment variables

```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
```

### 2. Start all services

```bash
cd docker
docker-compose up -d
```

### 3. Check service health

```bash
docker-compose ps
docker-compose logs -f api
```

### 4. Access services

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Useful Commands

### View logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f db
docker-compose logs -f redis
```

### Restart services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart api
```

### Stop services

```bash
docker-compose down
```

### Stop and remove volumes (clean slate)

```bash
docker-compose down -v
```

### Rebuild containers

```bash
docker-compose up --build
```

### Execute commands in containers

```bash
# Access API container shell
docker-compose exec api bash

# Access PostgreSQL
docker-compose exec db psql -U voiceai_user -d voiceai_db

# Access Redis CLI
docker-compose exec redis redis-cli
```

### Database migrations

```bash
# Inside API container
docker-compose exec api alembic upgrade head
docker-compose exec api alembic revision --autogenerate -m "description"
```

## Health Checks

All services have health checks configured:

- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **API**: HTTP GET `/api/health`

## Volumes

- `postgres_data`: PostgreSQL data persistence
- `redis_data`: Redis data persistence
- `prometheus_data`: Prometheus metrics storage
- `grafana_data`: Grafana dashboards and settings

## Network

All services run on the `voiceai_network` bridge network, allowing them to communicate using service names as hostnames.

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs [service-name]

# Check service status
docker-compose ps
```

### Database connection issues

```bash
# Verify PostgreSQL is running
docker-compose exec db pg_isready -U voiceai_user

# Check database logs
docker-compose logs db
```

### Redis connection issues

```bash
# Ping Redis
docker-compose exec redis redis-cli ping

# Check Redis logs
docker-compose logs redis
```

### Port already in use

If ports are already in use, edit `docker-compose.yml` to change the port mappings:

```yaml
ports:
  - "8001:8000"  # Changed from 8000:8000
```
