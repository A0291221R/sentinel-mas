FROM python:3.12-slim

WORKDIR /app

ARG SENTINEL_VERSION=0.1.0
RUN pip install --no-cache-dir sentinel-mas==${SENTINEL_VERSION}

COPY api_service/requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

RUN pip install --no-cache-dir boto3

COPY api_service/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

COPY api_service/ /app/api_service/

# Add non-root user (fixes SonarQube security hotspot)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV API_PORT=8000
EXPOSE ${API_PORT}

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import os; import requests; requests.get(f'http://localhost:{os.getenv(\"API_PORT\", \"8000\")}/health')" || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]