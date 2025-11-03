# Sentinel MAS API Service

REST API service that provides HTTP access to the Sentinel MAS package.

## Features

- 🔐 JWT-based authentication
- 👥 Role-based access control (RBAC)
- 🚀 Async query processing
- 📊 OpenAPI/Swagger documentation
- ✅ Comprehensive test suite
- 🐳 Docker support
- ☁️ AWS deployment ready

## Quick Start

### 1. Install Dependencies

```bash
# Install sentinel_mas package first
pip install -e .

# Install API dependencies
pip install -r requirements-api.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and set:
# - API_SECRET_KEY (generate with: openssl rand -hex 32)
# - SENTINEL_OPENAI_API_KEY
# - Other configuration
```

### 3. Run the Server

```bash
# Using the startup script
python scripts/start_api.py

# Or directly with uvicorn
uvicorn api_service.main:app --reload

# Or using the package module
python -m api_service.main
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## API Usage

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "password123"}'

# Response:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": "user-abc123",
  "user_role": "supervisor"
}
```

### Query Endpoint

```bash
# Send a query
curl -X POST http://localhost:8000/api/v1/queries \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "how to set tracking",
    "options": {},
    "context": {}
  }'

# Response:
{
  "output": "Response from Sentinel MAS...",
  "session_id": "api-abc123",
  "request_id": "req-xyz789",
  "elapsed_time": 2.45,
  "model_used": "gpt-4o-mini"
}
```

### Get User Info

```bash
curl -X GET http://localhost:8000/api/v1/queries/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Project Structure

```
api_service/
├── __init__.py
├── main.py                    # FastAPI application
├── config.py                  # Configuration
├── auth.py                    # JWT authentication
├── models.py                  # Pydantic models
├── routers/
│   ├── __init__.py
│   ├── auth.py               # Auth endpoints
│   ├── queries.py            # Query endpoints
│   └── admin.py              # Admin endpoints
└── services/
    ├── __init__.py
    └── sentinel_service.py   # Bridge to sentinel_mas
```

## Testing

```bash
# Run all API tests
pytest tests/test_api_service/ -v

# Run with coverage
pytest tests/test_api_service/ -v --cov=api_service

# Run specific test file
pytest tests/test_api_service/test_auth.py -v
```

## Docker

```bash
# Build image
docker build -f docker/Dockerfile.api -t sentinel-mas-api .

# Run container
docker run -p 8000:8000 \
  -e SENTINEL_OPENAI_API_KEY=sk-... \
  -e API_SECRET_KEY=your-secret \
  sentinel-mas-api
```

## Deployment

See [AWS Deployment Guide](../docs/AWS_DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy to AWS ECS

```bash
# Deploy to staging
git push origin develop

# Deploy to production
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Security

- Always use HTTPS in production
- Set a strong `API_SECRET_KEY`
- Use environment variables for secrets
- Enable CORS only for trusted origins
- Implement rate limiting
- Keep dependencies updated

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
