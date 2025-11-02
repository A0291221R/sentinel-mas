"""
Test Health and Basic Endpoints

Tests for basic API functionality, health checks, and documentation.
"""

from fastapi import status


class TestHealthEndpoints:
    """Test health check and basic endpoints"""

    def test_root_endpoint(self, client):
        """
        Test root endpoint returns API information

        Expected: 200 OK with service info
        """
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check required fields
        assert "service" in data
        assert "version" in data
        assert "status" in data

        # Check values
        assert data["status"] == "running"
        assert "docs" in data
        assert "health" in data

        print(f"✓ Root endpoint returned: {data}")

    def test_health_check(self, client):
        """
        Test health check endpoint

        Expected: 200 OK with healthy status
        """
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check structure
        assert "status" in data
        assert "service" in data
        assert "version" in data

        # Check values
        assert data["status"] == "healthy"
        assert len(data["service"]) > 0
        assert len(data["version"]) > 0

        print(f"✓ Health check: {data['status']}")

    def test_health_check_status_code_only(self, client):
        """Test health endpoint is accessible"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_openapi_docs_available(self, client):
        """
        Test OpenAPI (Swagger) documentation is available

        Expected: 200 OK with HTML page
        """
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")
        print("✓ Swagger docs available at /docs")

    def test_redoc_docs_available(self, client):
        """
        Test ReDoc documentation is available

        Expected: 200 OK with HTML page
        """
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")
        print("✓ ReDoc docs available at /redoc")

    def test_openapi_json_schema(self, client):
        """
        Test OpenAPI JSON schema is available

        Expected: 200 OK with valid OpenAPI schema
        """
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # Check OpenAPI structure
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

        # Check paths exist
        assert "/api/v1/auth/login" in data["paths"]
        assert "/api/v1/queries" in data["paths"]
        assert "/health" in data["paths"]

        print(f"✓ OpenAPI schema has {len(data['paths'])} endpoints")

    def test_invalid_endpoint(self, client):
        """
        Test accessing non-existent endpoint

        Expected: 404 Not Found
        """
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        print("✓ 404 for invalid endpoint")

    def test_cors_headers_present(self, client):
        """
        Test CORS headers are present in responses

        Expected: Access-Control headers in response
        """
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == status.HTTP_200_OK
        # CORS headers should be present
        # Note: Actual header names might be lowercase
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert any("access-control" in h for h in headers_lower.keys())
        print("✓ CORS headers present")
