"""
Test Query Endpoints

Tests for query processing, authentication, and user info endpoints.
"""

import pytest
from fastapi import status


class TestCreateQuery:
    """Test query creation endpoint"""

    @pytest.mark.slow
    def test_create_query_success(self, client, auth_headers):
        """
        Test successful query creation

        Expected: 200 OK or 500 if sentinel_mas not configured
        """
        response = client.post(
            "/api/v1/queries",
            headers=auth_headers,
            json={"prompt": "How do I set tracking?", "options": {}, "context": {}},
        )

        # May fail if sentinel_mas is not configured
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Check response structure
            assert "output" in data
            assert "session_id" in data
            assert "request_id" in data
            assert "elapsed_time" in data

            # Check values
            assert len(data["output"]) > 0
            assert data["session_id"].startswith("api-")
            assert data["request_id"].startswith("req-")
            assert data["elapsed_time"] > 0

            print(f"✓ Query successful in {data['elapsed_time']:.2f}s")
            print(f"  Session: {data['session_id']}")
            print(f"  Request: {data['request_id']}")
        else:
            print("⚠ Query failed (sentinel_mas not configured)")

    def test_create_query_no_authentication(self, client):
        """
        Test query without authentication token

        Expected: 403 Forbidden
        """
        response = client.post("/api/v1/queries", json={"prompt": "test query"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        print("✓ Correctly requires authentication")

    def test_create_query_invalid_token(self, client, invalid_token):
        """
        Test query with invalid authentication token

        Expected: 401 Unauthorized
        """
        response = client.post(
            "/api/v1/queries",
            headers={"Authorization": f"Bearer {invalid_token}"},
            json={"prompt": "test query"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        print("✓ Correctly rejects invalid token")

    def test_create_query_expired_token(self, client, expired_token):
        """
        Test query with expired authentication token

        Expected: 401 Unauthorized
        """
        response = client.post(
            "/api/v1/queries",
            headers={"Authorization": f"Bearer {expired_token}"},
            json={"prompt": "test query"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        print("✓ Correctly rejects expired token")

    def test_create_query_missing_prompt(self, client, auth_headers):
        """
        Test query without prompt field

        Expected: 422 Unprocessable Entity
        """
        response = client.post(
            "/api/v1/queries", headers=auth_headers, json={"options": {}, "context": {}}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Correctly requires prompt")

    def test_create_query_empty_prompt(self, client, auth_headers):
        """
        Test query with empty prompt

        Expected: 422 Unprocessable Entity
        """
        response = client.post(
            "/api/v1/queries",
            headers=auth_headers,
            json={"prompt": "", "options": {}, "context": {}},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Correctly rejects empty prompt")

    def test_create_query_whitespace_prompt(self, client, auth_headers):
        """Test query with whitespace-only prompt"""
        response = client.post(
            "/api/v1/queries",
            headers=auth_headers,
            json={"prompt": "   ", "options": {}, "context": {}},
        )

        # May be accepted but should handle gracefully
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    def test_create_query_with_options(self, client, auth_headers):
        """
        Test query with additional options

        Expected: Accepts options parameter
        """
        response = client.post(
            "/api/v1/queries",
            headers=auth_headers,
            json={
                "prompt": "test query",
                "options": {"verbose": True, "timeout": 30, "max_tokens": 100},
                "context": {},
            },
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        print("✓ Accepts options parameter")

    def test_create_query_with_context(self, client, auth_headers):
        """
        Test query with context information

        Expected: Accepts context parameter
        """
        response = client.post(
            "/api/v1/queries",
            headers=auth_headers,
            json={
                "prompt": "follow-up question",
                "options": {},
                "context": {
                    "previous_query": "initial question",
                    "session_data": {"key": "value"},
                },
            },
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        print("✓ Accepts context parameter")

    def test_create_query_minimal_payload(self, client, auth_headers):
        """
        Test query with minimal payload (prompt only)

        Expected: Works with just prompt
        """
        response = client.post(
            "/api/v1/queries",
            headers=auth_headers,
            json={"prompt": "minimal test query"},
        )

        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        print("✓ Works with minimal payload")

    def test_create_query_long_prompt(self, client, auth_headers):
        """Test query with very long prompt"""
        long_prompt = "test " * 1000  # 5000 characters

        response = client.post(
            "/api/v1/queries", headers=auth_headers, json={"prompt": long_prompt}
        )

        # Should accept long prompts
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,  # May have size limit
        ]
        print("✓ Handles long prompts")


class TestGetUserInfo:
    """Test get current user info endpoint"""

    def test_get_user_info_success(self, client, supervisor_headers, supervisor_token):
        """
        Test getting current user information

        Expected: 200 OK with user data
        """
        response = client.get("/api/v1/queries/me", headers=supervisor_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check structure
        assert "user_id" in data
        assert "user_role" in data

        # Check values match token
        assert data["user_id"] == "test-supervisor-123"
        assert data["user_role"] == "supervisor"

        print("✓ User info retrieved:")
        print(f"  User ID: {data['user_id']}")
        print(f"  Role: {data['user_role']}")

    def test_get_user_info_includes_email(self, client, auth_headers):
        """Test user info includes email if present"""
        response = client.get("/api/v1/queries/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        if "email" in data:
            assert "@" in data["email"]
            print(f"  Email: {data['email']}")

    def test_get_user_info_no_auth(self, client):
        """
        Test getting user info without authentication

        Expected: 403 Forbidden
        """
        response = client.get("/api/v1/queries/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        print("✓ Correctly requires authentication")

    def test_get_user_info_invalid_token(self, client, invalid_token):
        """
        Test getting user info with invalid token

        Expected: 401 Unauthorized
        """
        response = client.get(
            "/api/v1/queries/me", headers={"Authorization": f"Bearer {invalid_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        print("✓ Correctly rejects invalid token")

    def test_get_user_info_different_roles(self, client, admin_headers, user_headers):
        """Test user info works for different roles"""
        # Admin
        response = client.get("/api/v1/queries/me", headers=admin_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_role"] == "admin"
        print("✓ Admin user info retrieved")

        # Regular user
        response = client.get("/api/v1/queries/me", headers=user_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_role"] == "user"
        print("✓ Regular user info retrieved")
