"""
Authentication Routes

Handles login and authentication endpoints.
"""

import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status

from ..auth import create_access_token
from ..config import get_api_config
from ..models import LoginRequest, LoginResponse

api_config = get_api_config()
router = APIRouter(prefix="/auth", tags=["Authentication"])

MOCK_USERS = {
    "operator@example.com": {"password": "operator123", "user_role": "operator"},
    "admin@example.com": {"password": "admin123", "user_role": "admin"},
    "supervisor@example.com": {"password": "supervisor123", "user_role": "supervisor"},
    "viewer@example.com": {"password": "viewer123", "user_role": "viewer"},
}


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest) -> LoginResponse:
    """
    Login endpoint - authenticate user and return JWT token

    **TODO: Replace with actual database authentication**

    Currently uses mock authentication. In production, you should:
    1. Query database for user by email
    2. Verify password hash (use bcrypt)
    3. Return user data and token

    Args:
        credentials: LoginRequest with email and password

    Returns:
        LoginResponse with access_token and user info

    Raises:
        401 Unauthorized: If credentials are invalid

    Example Request:
        POST /api/v1/auth/login
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Example Response:
        {
            "access_token": "eyJhbGc...",
            "token_type": "bearer",
            "user_id": "user-abc123",
            "user_role": "supervisor"
        }
    """
    # Mock authentication - REPLACE WITH YOUR DATABASE LOGIC
    if credentials.email and credentials.password:
        # TODO: Replace this with actual database lookup
        # Example:
        # user = db.query(User).filter(User.email == credentials.email).first()
        # if not user or not verify_password(
        #   credentials.password, user.hashed_password):
        #     raise HTTPException(401, "Invalid credentials")

        user_record = MOCK_USERS.get(credentials.email)
        if not user_record or user_record["password"] != credentials.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Mock user_id generation
        user_id = f"user-{uuid.uuid4().hex[:10]}"

        # Create JWT
        access_token_expires = timedelta(minutes=api_config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "user_id": user_id,
                "user_role": user_record["user_role"],
                "email": credentials.email,
            },
            expires_delta=access_token_expires,
        )

        return LoginResponse(
            access_token=access_token,
            user_id=user_id,
            user_role=user_record["user_role"],
        )

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid query param"
    )


@router.post("/refresh")
async def refresh_token() -> None:
    """
    Refresh access token

    TODO: Implement refresh token logic

    In production, implement:
    1. Accept refresh token
    2. Validate refresh token
    3. Issue new access token
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token not implemented yet",
    )
