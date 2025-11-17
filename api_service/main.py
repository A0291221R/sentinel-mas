"""
Sentinel MAS API Service

Main FastAPI application entry point.
"""

import os
from typing import Any, Dict

from aws_xray_sdk.core import patch_all, xray_recorder
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

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

# Only enable X-Ray in ECS/production
IS_XRAY_ENABLED = os.getenv("AWS_XRAY_DAEMON_ADDRESS") is not None
if IS_XRAY_ENABLED:
    # Patch libraries only in production
    patch_all()

    # Configure X-Ray
    xray_recorder.configure(
        service=os.getenv("AWS_XRAY_TRACING_NAME", "sentinel-v2-api"),
        daemon_address=os.getenv("AWS_XRAY_DAEMON_ADDRESS", "127.0.0.1:2000"),
        sampling=True,
    )

    # Custom X-Ray Middleware
    class XRayMiddleware(BaseHTTPMiddleware):
        async def dispatch(
            self, request: Request, call_next: RequestResponseEndpoint
        ) -> Any:
            # Start X-Ray segment
            segment = xray_recorder.begin_segment(
                name=os.getenv("AWS_XRAY_TRACING_NAME", "sentinel-v2-api"),
                sampling=True,
            )

            try:
                # Add request metadata
                segment.put_http_meta("url", str(request.url))
                segment.put_http_meta("method", request.method)
                segment.put_http_meta(
                    "user_agent", request.headers.get("user-agent", "")
                )

                # Process request
                response = await call_next(request)

                # Add response metadata
                segment.put_http_meta("status", response.status_code)

                return response

            except Exception as e:
                # Record exception
                segment.put_annotation("error", str(e))
                raise

            finally:
                # Always end segment
                xray_recorder.end_segment()

    # Add X-Ray middleware using ASGI
    app.add_middleware(XRayMiddleware)


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
