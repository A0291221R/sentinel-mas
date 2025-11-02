"""
API Service Test Configuration

Fixtures specific to testing the API service.
"""

from datetime import timedelta

import pytest
from api_service.auth import create_access_token
from api_service.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def api_client():
    """
    Create a test client for the API

    Module-scoped: Created once per test module.

    Yields:
        TestClient: FastAPI test client
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def client(api_client):
    """Alias for api_client for backward compatibility"""
    return api_client


@pytest.fixture(scope="module")
def supervisor_token():
    """
    Create a supervisor authentication token

    Returns:
        str: Valid JWT token with supervisor role
    """
    token = create_access_token(
        data={
            "user_id": "test-supervisor-123",
            "user_role": "supervisor",
            "email": "supervisor@example.com",
        },
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture(scope="module")
def admin_token():
    """
    Create an admin authentication token

    Returns:
        str: Valid JWT token with admin role
    """
    token = create_access_token(
        data={
            "user_id": "test-admin-123",
            "user_role": "admin",
            "email": "admin@example.com",
        },
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture(scope="module")
def user_token():
    """
    Create a regular user authentication token

    Returns:
        str: Valid JWT token with user role
    """
    token = create_access_token(
        data={
            "user_id": "test-user-123",
            "user_role": "user",
            "email": "user@example.com",
        },
        expires_delta=timedelta(hours=1),
    )
    return token


@pytest.fixture(scope="module")
def auth_token(supervisor_token):
    """Alias for supervisor_token"""
    return supervisor_token


@pytest.fixture
def supervisor_headers(supervisor_token):
    """Authorization headers with supervisor token"""
    return {
        "Authorization": f"Bearer {supervisor_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def admin_headers(admin_token):
    """Authorization headers with admin token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def user_headers(user_token):
    """Authorization headers with user token"""
    return {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}


@pytest.fixture
def auth_headers(supervisor_headers):
    """Alias for supervisor_headers"""
    return supervisor_headers


@pytest.fixture
def invalid_token():
    """Invalid JWT token for testing"""
    return "invalid.jwt.token"


@pytest.fixture
def expired_token():
    """Expired JWT token for testing"""
    token = create_access_token(
        data={"user_id": "expired-user", "user_role": "user"},
        expires_delta=timedelta(seconds=-1),
    )
    return token
