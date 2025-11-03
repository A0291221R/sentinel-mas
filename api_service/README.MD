### 1. Request Flow

Client Request
    ↓
FastAPI (main.py)
    ↓
Router (auth.py / queries.py / admin.py)
    ↓
Auth Middleware (auth.py) - Validates JWT
    ↓
Service Layer (sentinel_service.py)
    ↓
Sentinel MAS Package (CreateCrew)
    ↓
Response back to Client


### 2. Authentication Flow
# Step 1: Login
POST /api/v1/auth/login
{
    "username": "user@example.com",
    "password": "password123"
}

↓ auth.py validates credentials
↓ Creates JWT token

Response:
{
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user_id": "user-abc123",
    "user_role": "supervisor"
}

# Step 2: Use token for authenticated requests
POST /api/v1/queries
Headers:
    Authorization: Bearer eyJhbGc...
Body:
    {
        "prompt": "How to set tracking?"
    }

↓ get_current_user() extracts and validates token
↓ Creates AuthContext
↓ Calls sentinel_service
↓ Returns result

### 3. Configuration Loading
# When API starts:

1. main.py imports get_api_config()
2. get_api_config() creates APIConfig instance
3. APIConfig reads from:
   - .env.api (API-specific config)
   - .env.shared (shared config)
4. Validates required settings
5. Returns cached config (lru_cache)

# Config is loaded once and reused


### 4. Service Layer Pattern
# Why we have a service layer:

API Layer (routers/)
    ↓ HTTP concerns (requests, responses, validation)
    
Service Layer (services/)
    ↓ Business logic (processing, orchestration)
    
Package Layer (sentinel_mas)
    ↓ Core functionality (agents, tools)

# Benefits:
# - Clean separation of concerns
# - Easy to test
# - Can reuse service in different APIs
# - Swap out package without changing API


### Running the API
~~~bash
# Option 1: Using the startup script (Recommended)
python scripts/start_api.py

# Option 2: Using uvicorn directly
uvicorn api_service.main:app --reload

# Option 3: Using the module
python -m api_service.main

# Option 4: Using Docker
docker build -f docker/Dockerfile.api -t sentinel-api .
docker run -p 8000:8000 sentinel-api


### Testing the API
# 1. Check if it's running
curl http://localhost:8000/health
# Response
{
  "status": "healthy",
  "service": "Sentinel MAS API",
  "version": "1.0.0"
}

#  2. Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123"
  }'
# Response 
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "user-abc123",
  "user_role": "supervisor"
}

# 3. Send a query
TOKEN="your-token-here"

curl -X POST http://localhost:8000/api/v1/queries \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How do I set tracking?"
  }'

# Response
{
  "user_id": "user-abc123",
  "user_role": "supervisor",
  "username": "user@example.com",
  "token_expires": "2024-01-15T10:30:00"
}


netstat -ano | findstr :8000


Production Deployment
See the AWS deployment guide for:

Docker containerization
ECS deployment
Load balancing
Auto-scaling
Monitoring
Logging