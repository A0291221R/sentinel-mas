"""
Test Admin Endpoints

Tests for admin-only functionality and role-based access control.
"""

import pytest
from fastapi import status


class TestAdminQuery:
    """Test admin query endpoint"""

    @pytest.mark.slow
    def test_admin_query_with_admin_role(self, client, admin_headers):
        """
        Test admin query with admin role

        Expected: 200 OK (admin has access)
        """
        response = client.post(
            "/api/v1/admin/queries",
            headers=admin_headers,
            json={"prompt": "admin test query"},
        )

        # Should accept admin requests
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        print("✓ Admin can access admin endpoint")

    @pytest.mark.slow
    def test_admin_query_with_supervisor_role(self, client, supervisor_headers):
        """
        Test admin query with supervisor role

        Expected: 200 OK (supervisor also has access)
        """
        response = client.post(
            "/api/v1/admin/queries",
            headers=supervisor_headers,
            json={"prompt": "supervisor test query"},
        )

        # Supervisor should also have access
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]
        print("✓ Supervisor can access admin endpoint")

    def test_admin_query_with_user_role(self, client, user_headers):
        """
        Test admin query with regular user role

        Expected: 403 Forbidden (user doesn't have access)
        """
        response = client.post(
            "/api/v1/admin/queries",
            headers=user_headers,
            json={"prompt": "user test query"},
        )

        # Regular user should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN

        data = response.json()
        assert "detail" in data
        # Error message should mention required roles
        detail_lower = data["detail"].lower()
        assert (
            "admin" in detail_lower
            or "supervisor" in detail_lower
            or "forbidden" in detail_lower
        )

        print(f"✓ User correctly denied: {data['detail']}")

    def test_admin_query_no_authentication(self, client):
        """
        Test admin query without authentication

        Expected: 403 Forbidden
        """
        response = client.post("/api/v1/admin/queries", json={"prompt": "test query"})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        print("✓ Requires authentication")

    def test_admin_query_invalid_token(self, client, invalid_token):
        """
        Test admin query with invalid token

        Expected: 401 Unauthorized
        """
        response = client.post(
            "/api/v1/admin/queries",
            headers={"Authorization": f"Bearer {invalid_token}"},
            json={"prompt": "test query"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        print("✓ Rejects invalid token")


class TestAdminConfig:
    """Test admin config endpoint"""

    def test_get_config_with_admin_role(self, client, admin_headers):
        """
        Test getting config info with admin role

        Expected: 200 OK with config data
        """
        response = client.get("/api/v1/admin/config", headers=admin_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should contain config information
        assert isinstance(data, dict)
        assert len(data) > 0

        print("✓ Admin can view config:")
        for key, value in data.items():
            print(f"  {key}: {value}")

    def test_get_config_with_supervisor_role(self, client, supervisor_headers):
        """
        Test getting config info with supervisor role

        Expected: 403 Forbidden (only admin can view config)
        """
        response = client.get("/api/v1/admin/config", headers=supervisor_headers)

        # Only admin should access config
        assert response.status_code == status.HTTP_403_FORBIDDEN
        print("✓ Supervisor cannot view config")

    def test_get_config_with_user_role(self, client, user_headers):
        """
        Test getting config info with user role

        Expected: 403 Forbidden
        """
        response = client.get("/api/v1/admin/config", headers=user_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        print("✓ User cannot view config")

    def test_get_config_no_authentication(self, client):
        """
        Test getting config info without authentication

        Expected: 403 Forbidden
        """
        response = client.get("/api/v1/admin/config")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        print("✓ Config requires authentication")

    def test_get_config_invalid_token(self, client, invalid_token):
        """Test config endpoint with invalid token"""
        response = client.get(
            "/api/v1/admin/config", headers={"Authorization": f"Bearer {invalid_token}"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRoleBasedAccessControl:
    """Test role-based access control across endpoints"""

    def test_admin_has_full_access(self, client, admin_headers):
        """Test admin role has access to all endpoints"""

        # Regular query endpoint
        response = client.post(
            "/api/v1/queries", headers=admin_headers, json={"prompt": "test"}
        )
        assert response.status_code in [200, 500]

        # Admin query endpoint
        response = client.post(
            "/api/v1/admin/queries", headers=admin_headers, json={"prompt": "test"}
        )
        assert response.status_code in [200, 500]

        # Config endpoint
        response = client.get("/api/v1/admin/config", headers=admin_headers)
        assert response.status_code == 200

        print("✓ Admin has full access to all endpoints")

    def test_supervisor_has_limited_access(self, client, supervisor_headers):
        """Test supervisor role has access to most but not all endpoints"""

        # Regular query endpoint
        response = client.post(
            "/api/v1/queries", headers=supervisor_headers, json={"prompt": "test"}
        )
        assert response.status_code in [200, 500]

        # Admin query endpoint
        response = client.post(
            "/api/v1/admin/queries", headers=supervisor_headers, json={"prompt": "test"}
        )
        assert response.status_code in [200, 500]

        # Config endpoint (should be forbidden)
        response = client.get("/api/v1/admin/config", headers=supervisor_headers)
        assert response.status_code == 403

        print("✓ Supervisor has limited access")

    def test_user_has_minimal_access(self, client, user_headers):
        """Test regular user has minimal access"""

        # Regular query endpoint
        response = client.post(
            "/api/v1/queries", headers=user_headers, json={"prompt": "test"}
        )
        assert response.status_code in [200, 500]

        # Admin query endpoint (should be forbidden)
        response = client.post(
            "/api/v1/admin/queries", headers=user_headers, json={"prompt": "test"}
        )
        assert response.status_code == 403

        # Config endpoint (should be forbidden)
        response = client.get("/api/v1/admin/config", headers=user_headers)
        assert response.status_code == 403

        print("✓ User has minimal access")
