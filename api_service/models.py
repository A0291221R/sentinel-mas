"""
API Request/Response Models

Pydantic models for API requests and responses.
These provide validation and documentation.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    Login request model

    Example:
        {
            "username": "user@example.com",
            "password": "password123"
        }
    """

    username: str = Field(..., description="User username")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """
    Login response model

    Example:
        {
            "access_token": "eyJhbGc...",
            "token_type": "bearer",
            "user_id": "user-abc123",
            "user_role": "supervisor"
        }
    """

    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_role: str


class QueryRequest(BaseModel):
    """
    Query request model

    Example:
        {
            "prompt": "How do I set tracking?",
            "options": {"verbose": true},
            "context": {"previous_query": "..."}
        }
    """

    prompt: str = Field(..., description="User query", min_length=1)
    options: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional options for query processing"
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional context for the query"
    )


class QueryResponse(BaseModel):
    """
    Query response model

    Example:
        {
            "output": "To set tracking, you need to...",
            "session_id": "api-abc123",
            "request_id": "req-xyz789",
            "elapsed_time": 2.45,
            "model_used": "gpt-4o-mini"
        }
    """

    output: str  # The actual response from Sentinel MAS
    session_id: str  # Session identifier
    request_id: str  # Request identifier
    elapsed_time: float  # Time taken to process (seconds)
    model_used: Optional[str] = None  # Model that was used


class UserInfo(BaseModel):
    """
    User information model

    Example:
        {
            "user_id": "user-abc123",
            "user_role": "supervisor",
            "username": "user@example.com",
            "token_expires": "2024-01-15T10:30:00"
        }
    """

    user_id: str
    user_role: str
    username: Optional[str] = None
    token_expires: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Error response model

    Example:
        {
            "detail": "Invalid credentials",
            "error_code": "AUTH_ERROR"
        }
    """

    detail: str
    error_code: Optional[str] = None


class HealthResponse(BaseModel):
    """
    Health check response

    Example:
        {
            "status": "healthy",
            "service": "Sentinel MAS API",
            "version": "1.0.0"
        }
    """

    status: str
    service: str
    version: str
