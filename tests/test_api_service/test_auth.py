"""
Test Authentication Endpoints

Tests for login, token generation, and authentication flows.
"""

from fastapi import status


class TestAuthLogin:
    """Test login endpoint"""

    def test_login_success_with_valid_credentials(self, client):
        """
        Test successful login with valid credentials

        Expected: 200 OK with access token
        """
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "supervisor@example.com", "password": "supervisor123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert "user_role" in data

        # Check values
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20  # JWT tokens are long
        assert len(data["user_id"]) > 0
        assert data["user_role"] in ["admin", "supervisor", "user"]

        print(f"✓ Login successful, token: {data['access_token'][:20]}...")
        print(f"  User ID: {data['user_id']}")
        print(f"  Role: {data['user_role']}")

    def test_login_with_different_email(self, client):
        """Test login works with different email addresses"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "another@example.com", "password": "pass456"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "access_token" not in data

    def test_login_missing_email(self, client):
        """
        Test login with missing email field

        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/v1/auth/login", json={"password": "password123"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Correctly rejects missing email")

    def test_login_missing_password(self, client):
        """
        Test login with missing password field

        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/v1/auth/login", json={"email": "test@example.com"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Correctly rejects missing password")

    def test_login_both_fields_missing(self, client):
        """
        Test login with both fields missing

        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/v1/auth/login", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_empty_email(self, client):
        """
        Test login with empty email

        Expected: 422 Unprocessable Entity
        """
        response = client.post(
            "/api/v1/auth/login", json={"email": "", "password": "password123"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Correctly rejects empty email")

    def test_login_empty_password(self, client):
        """
        Test login with empty password

        Expected: 422 Unprocessable Entity
        """
        response = client.post(
            "/api/v1/auth/login", json={"email": "test@example.com", "password": ""}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Correctly rejects empty password")

    def test_login_both_fields_empty(self, client):
        """
        Test login with both fields empty

        Expected: 422 Unprocessable Entity
        """
        response = client.post("/api/v1/auth/login", json={"email": "", "password": ""})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_invalid_json(self, client):
        """
        Test login with malformed JSON

        Expected: 422 Unprocessable Entity
        """
        response = client.post(
            "/api/v1/auth/login",
            data="this is not json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ Correctly rejects invalid JSON")

    def test_login_extra_fields_ignored(self, client):
        """
        Test login with extra fields (should be ignored)

        Expected: 200 OK (extra fields ignored)
        """
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "viewer@example.com",
                "password": "viewer123",
                "extra_field": "should be ignored",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        print("✓ Extra fields ignored gracefully")


class TestAuthRefresh:
    """Test token refresh endpoint"""

    def test_refresh_token_not_implemented(self, client):
        """
        Test refresh token endpoint returns not implemented

        Expected: 501 Not Implemented
        """
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
        data = response.json()
        assert "detail" in data
        print(f"✓ Refresh endpoint: {data['detail']}")

    def test_refresh_with_token_not_implemented(self, client, auth_token):
        """Test refresh with valid token still not implemented"""
        response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
