import os
import logging
import sys
import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    stream=sys.stdout,
)

SERVICE_NAME = os.getenv("SERVICE_NAME", "centralized-server")

if __name__ == "__main__":
    # Run uvicorn directly
    uvicorn.run(
        "app.webapi_service:app",
        host="0.0.0.0",
        port=8100,
        log_level="info"
    )