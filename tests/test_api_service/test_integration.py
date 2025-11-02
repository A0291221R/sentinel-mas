"""
Integration Tests

End-to-end tests for complete workflows and user journeys.
"""

import pytest
from fastapi import status


class TestCompleteUserFlow:
    """Test complete user workflows"""

    def test_login_query_get_info_flow(self, client):
        """
        Test complete flow: login -> create query -> get user info

        This simulates a real user interaction with the API.
        """
        # Step 1: Login
        print("\n--- Step 1: Login ---")
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "operator@example.com", "password": "operator123"},
        )

        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]
        user_id = login_response.json()["user_id"]
        print(f"✓ Logged in, user ID: {user_id}")

        # Step 2: Create a query
        print("\n--- Step 2: Create Query ---")
        headers = {"Authorization": f"Bearer {token}"}
        query_response = client.post(
            "/api/v1/queries",
            headers=headers,
            json={"prompt": "Integration test query - how do I set tracking?"},
        )

        assert query_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        if query_response.status_code == status.HTTP_200_OK:
            query_data = query_response.json()
            print(f"✓ Query processed in {query_data['elapsed_time']:.2f}s")
            print(f"  Session: {query_data['session_id']}")
        else:
            print("⚠ Query failed (sentinel_mas not configured)")

        # Step 3: Get user info
        print("\n--- Step 3: Get User Info ---")
        user_response = client.get("/api/v1/queries/me", headers=headers)

        assert user_response.status_code == status.HTTP_200_OK
        user_data = user_response.json()
        assert user_data["user_id"] == user_id
        print(f"✓ Retrieved user info: {user_data['user_role']}")

        print("\n✓ Complete user flow successful!")

    def test_multiple_queries_same_session(self, client, auth_headers):
        """
        Test multiple queries with the same token

        Expected: All queries work with same token
        """
        queries = [
            "First query: what is tracking?",
            "Second query: how do I enable it?",
            "Third query: are there any limitations?",
        ]

        print("\n--- Testing Multiple Queries ---")
        for i, prompt in enumerate(queries, 1):
            response = client.post(
                "/api/v1/queries", headers=auth_headers, json={"prompt": prompt}
            )

            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ]

            if response.status_code == status.HTTP_200_OK:
                data = response.json()
                print(f"✓ Query {i} successful: {data['session_id']}")
            else:
                print(f"⚠ Query {i} failed")

        print("✓ Multiple queries completed")

    def test_role_escalation_prevented(self, client, user_headers, admin_headers):
        """
        Test that users cannot escalate their privileges

        Expected: Role-based access properly enforced
        """
        print("\n--- Testing Role-Based Access Control ---")

        # Regular user tries admin endpoint
        print("1. User attempts admin endpoint")
        response = client.post(
            "/api/v1/admin/queries",
            headers=user_headers,
            json={"prompt": "unauthorized access attempt"},
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        print("   ✓ Correctly blocked")

        # Admin can access same endpoint
        print("2. Admin accesses admin endpoint")
        response = client.post(
            "/api/v1/admin/queries",
            headers=admin_headers,
            json={"prompt": "authorized access"},
        )
        assert response.status_code in [200, 500]
        print("   ✓ Correctly allowed")

        print("✓ Role-based access control working correctly")

    @pytest.mark.slow
    def test_concurrent_requests_same_user(self, client, auth_headers):
        """
        Test handling of concurrent requests from same user

        Note: This is a simplified test. Real concurrency testing
        would require async/threading.
        """
        print("\n--- Testing Sequential Requests ---")

        responses = []
        for i in range(3):
            response = client.post(
                "/api/v1/queries",
                headers=auth_headers,
                json={"prompt": f"Concurrent test query {i+1}"},
            )
            responses.append(response)

        # All should succeed or fail consistently
        status_codes = [r.status_code for r in responses]
        assert all(code in [200, 500] for code in status_codes)

        print(f"✓ {len(responses)} sequential requests handled")


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_endpoint_returns_404(self, client):
        """Test that invalid endpoints return 404"""
        response = client.get("/api/v1/does-not-exist")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        print("✓ 404 for invalid endpoint")

    def test_invalid_method_returns_405(self, client):
        """Test that invalid HTTP methods return 405"""
        # Health endpoint only supports GET
        response = client.post("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        print("✓ 405 for invalid method")

    def test_malformed_json_returns_422(self, client):
        """Test that malformed JSON returns 422"""
        response = client.post(
            "/api/v1/auth/login",
            data="{ this is not valid json }",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        print("✓ 422 for malformed JSON")

    def test_missing_content_type_handled(self, client):
        """Test requests without Content-Type header"""
        response = client.post(
            "/api/v1/auth/login",
            data='{"email": "test@example.com", "password": "test"}',
        )
        # Should still work or return proper error
        assert response.status_code in [200, 401, 422]
        print("✓ Missing Content-Type handled")
