#!/usr/bin/env python3
"""
Startup script for Sentinel MAS API

This is the recommended way to start the API server.
"""

import uvicorn
from api_service.config import get_api_config

# Load configuration
config = get_api_config()

if __name__ == "__main__":
    print("=" * 70)
    print(f"Starting {config.PROJECT_NAME} v{config.VERSION}")
    print("=" * 70)
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"Host: {config.HOST}")
    print(f"Port: {config.PORT}")
    print(f"Debug: {config.DEBUG}")
    print("=" * 70)

    # Start the server
    uvicorn.run(
        "api_service.main:app",  # Import path to FastAPI app
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,  # Auto-reload on code changes in debug mode
        log_level="info",
    )
