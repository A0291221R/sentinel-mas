"""
Sentinel MAS API Service

Main FastAPI application entry point.
"""

from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_api_config
from .models import HealthResponse
from .routers import admin, auth, queries

# Get API configuration
config = get_api_config()

# Create FastAPI application
app = FastAPI(
    title=config.PROJECT_NAME,
    version=config.VERSION,
    description="REST API for Sentinel MAS - Multi-Agent System",
    openapi_url=f"{config.V1_PREFIX}/openapi.json",
    debug=config.DEBUG,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
)

# CORS middleware - allows cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,  # Which origins can access
    allow_credentials=True,  # Allow cookies
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
# Each router handles a group of related endpoints
app.include_router(auth.router, prefix=config.V1_PREFIX)
app.include_router(queries.router, prefix=config.V1_PREFIX)
app.include_router(admin.router, prefix=config.V1_PREFIX)


@app.on_event("startup")
async def startup_event() -> None:
    """
    Run on application startup

    This is called once when the server starts.
    Good place for:
    - Database connections
    - Loading models
    - Warming caches
    """
    print(f"Starting {config.PROJECT_NAME} v{config.VERSION}")
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"API available at: http://{config.HOST}:{config.PORT}")
    print(f"Documentation at: http://{config.HOST}:{config.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Run on application shutdown

    This is called when the server stops.
    Good place for:
    - Closing database connections
    - Saving state
    - Cleanup
    """
    print(f"Shutting down {config.PROJECT_NAME}")


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint

    Returns basic API information and links to documentation.

    Example Response:
        {
            "service": "Sentinel MAS API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "health": "/health"
        }
    """
    return {
        "service": config.PROJECT_NAME,
        "version": config.VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint

    Used by:
    - Load balancers to check if service is alive
    - Monitoring systems
    - Docker healthchecks

    Returns:
        HealthResponse with status information

    Example Response:
        {
            "status": "healthy",
            "service": "Sentinel MAS API",
            "version": "1.0.0"
        }
    """
    return HealthResponse(
        status="healthy",
        service=config.PROJECT_NAME,
        version=config.VERSION,
    )


# Entry point for running directly with Python
if __name__ == "__main__":
    import uvicorn

    # Run the server
    uvicorn.run(
        "api_service.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info",
    )
