FROM python:3.12-slim

WORKDIR /app

# Install sentinel-mas package (NO .env files included)
ARG SENTINEL_VERSION=0.1.0
RUN pip install --no-cache-dir sentinel-mas==${SENTINEL_VERSION}

# Install API dependencies
COPY api_service/requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt

# Install boto3 for AWS SSM
RUN pip install --no-cache-dir boto3

# Copy entrypoint script
COPY api_service/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy application code
COPY api_service/ /app/api_service/

# .env files will be created by entrypoint script or mounted at runtime
# NOT copied from build context

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "api_service.main:app", "--host", "0.0.0.0", "--port", "8000"]