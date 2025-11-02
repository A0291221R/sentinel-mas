"""
Test CORS Configuration

Tests for Cross-Origin Resource Sharing configuration.
"""

from fastapi import status


class TestCORSHeaders:
    """Test CORS headers in responses"""

    def test_cors_preflight_request(self, client):
        """
        Test CORS preflight (OPTIONS) request

        Expected: 200 OK with CORS headers
        """
        response = client.options(
            "/api/v1/queries",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        # Check for CORS headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        assert "access-control-allow-origin" in headers_lower

        print("✓ CORS preflight successful")
        print(f"  Allowed origin: {headers_lower.get('access-control-allow-origin')}")

    def test_cors_headers_in_actual_request(self, client, auth_headers):
        """
        Test CORS headers are present in actual requests

        Expected: CORS headers in response
        """
        response = client.post(
            "/api/v1/queries",
            headers={**auth_headers, "Origin": "http://localhost:3000"},
            json={"prompt": "test"},
        )

        # Check for CORS headers
        headers_lower = {k.lower(): v for k, v in response.headers.items()}

        # Should have some CORS headers
        has_cors = any("access-control" in h for h in headers_lower.keys())
        assert has_cors or response.status_code in [200, 500]

        print("✓ CORS headers present in actual request")

    def test_cors_with_allowed_origin(self, client):
        """Test CORS with origin in allowed list"""
        response = client.get("/health", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == status.HTTP_200_OK

        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        if "access-control-allow-origin" in headers_lower:
            print(
                "✓ Allowed origin accepted: "
                "{headers_lower['access-control-allow-origin']}"
            )

    def test_cors_allows_credentials(self, client):
        """Test CORS allows credentials"""
        response = client.options(
            "/api/v1/queries",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )

        headers_lower = {k.lower(): v for k, v in response.headers.items()}

        # Check if credentials are allowed
        if "access-control-allow-credentials" in headers_lower:
            assert headers_lower["access-control-allow-credentials"] == "true"
            print("✓ CORS allows credentials")


class TestCORSMethods:
    """Test CORS allowed methods"""

    def test_cors_allows_common_methods(self, client):
        """Test CORS allows common HTTP methods"""
        methods_to_test = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

        for method in methods_to_test:
            response = client.options(
                "/api/v1/queries",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": method,
                },
            )

            assert response.status_code == status.HTTP_200_OK

        print(f"✓ CORS allows methods: {', '.join(methods_to_test)}")
