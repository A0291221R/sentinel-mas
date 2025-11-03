"""
JWT Authentication Module

Handles JWT token creation, validation, and user authentication.
"""

import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import get_api_config

api_config = get_api_config()
security = HTTPBearer()  # Expects "Authorization: Bearer <token>" header


class TokenData(BaseModel):
    """
    JWT token payload data

    This is what gets stored inside the JWT token.
    """

    user_id: str  # Unique user identifier
    user_role: str  # User's role (admin, supervisor, user)
    username: Optional[str] = None  # User's username
    exp: Optional[datetime] = None  # Token expiration time


class AuthContext(BaseModel):
    """
    Authenticated user context

    This is passed to services after authentication.
    Contains user info + request tracking.
    """

    user_id: str
    user_role: str
    username: Optional[str] = None
    session_id: str  # Unique session identifier
    request_id: str  # Unique request identifier


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Dictionary of data to encode in token (user_id, user_role, etc)
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token

    Example:
        token = create_access_token({
            "user_id": "user123",
            "user_role": "supervisor",
            "username": "user@example.com"
        })
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=api_config.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add expiration to token payload
    to_encode.update({"exp": expire, "iat": time.time(), "jti": str(uuid.uuid4())})

    # Encode and sign the token
    encoded_jwt = jwt.encode(
        to_encode,
        api_config.SECRET_KEY,  # Secret key for signing
        algorithm=api_config.ALGORITHM,  # HS256
    )
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData: Decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Decode and verify token
        payload = jwt.decode(
            token, api_config.SECRET_KEY, algorithms=[api_config.ALGORITHM]
        )

        # Extract user data from payload
        user_id: str = payload.get("user_id", "")
        user_role: str = payload.get("user_role", "")
        username: str = payload.get("username", "")

        # Validate required fields
        if user_id is None or user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return TokenData(
            user_id=user_id,
            user_role=user_role,
            username=username,
            exp=datetime.fromtimestamp(payload.get("exp", ""), tz=timezone.utc),
        )

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Dependency to extract and validate current user from JWT

    This is used in route handlers:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}

    Args:
        credentials: HTTP Bearer token from request header

    Returns:
        TokenData: Validated user data

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    token = credentials.credentials
    return decode_token(token)


def require_role(*allowed_roles: str) -> Any:
    """
    Dependency factory for role-based access control

    Creates a dependency that checks if user has required role.

    Usage:
        @app.get("/admin")
        async def admin_route(user: TokenData = Depends(require_role("admin"))):
            return {"message": "Admin only"}

    Args:
        *allowed_roles: Variable number of allowed role strings

    Returns:
        Function: Dependency function that checks user role
    """

    def role_checker(token_data: TokenData = Depends(get_current_user)) -> TokenData:
        if token_data.user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required roles: {', '.join(allowed_roles)}",
            )
        return token_data

    return role_checker
