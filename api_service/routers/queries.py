"""
Query Routes

Handles query processing endpoints.
"""

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends

from ..auth import AuthContext, TokenData, get_current_user
from ..models import QueryRequest, QueryResponse, UserInfo
from ..services.sentinel_service import SentinelService, get_sentinel_service

router = APIRouter(prefix="/queries", tags=["Queries"])


@router.post("", response_model=QueryResponse)
async def create_query(
    request: QueryRequest,
    current_user: TokenData = Depends(get_current_user),
    sentinel_service: SentinelService = Depends(get_sentinel_service),
) -> QueryResponse:
    """
    Process a user query with JWT authentication

    This is the main endpoint for sending queries to Sentinel MAS.
    Requires valid JWT token in Authorization header.

    Args:
        request: QueryRequest with prompt and optional context
        current_user: Extracted from JWT token (automatic)
        sentinel_service: Injected service (automatic)

    Returns:
        QueryResponse with output and metadata

    Example Request:
        POST /api/v1/queries
        Headers:
            Authorization: Bearer eyJhbGc...
        Body:
            {
                "prompt": "How do I set tracking?",
                "options": {"verbose": true},
                "context": {}
            }

    Example Response:
        {
            "output": "To set tracking, you need to...",
            "session_id": "api-abc123",
            "request_id": "req-xyz789",
            "elapsed_time": 2.45,
            "model_used": "gpt-4o-mini"
        }
    """
    # Create auth context from JWT token data
    auth_context = AuthContext(
        user_id=current_user.user_id,
        user_role=current_user.user_role,
        email=current_user.email,
        session_id=f"api-{uuid.uuid4().hex[:10]}",
        request_id=f"req-{uuid.uuid4().hex[:10]}",
    )

    # Process query through service layer
    result = await sentinel_service.process_query(
        prompt=request.prompt,
        auth_context=auth_context,
        options=request.options,
        context=request.context,
    )

    return QueryResponse(**result)


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
) -> UserInfo:
    """
    Get current authenticated user information

    Returns information about the currently authenticated user
    based on their JWT token.

    Args:
        current_user: Extracted from JWT token (automatic)

    Returns:
        UserInfo with user_id, role, email, etc.

    Example Request:
        GET /api/v1/queries/me
        Headers:
            Authorization: Bearer eyJhbGc...

    Example Response:
        {
            "user_id": "user-abc123",
            "user_role": "supervisor",
            "email": "user@example.com",
            "token_expires": "2024-01-15T10:30:00"
        }
    """
    return UserInfo(
        user_id=current_user.user_id,
        user_role=current_user.user_role,
        email=current_user.email,
        token_expires=current_user.exp.isoformat() if current_user.exp else None,
    )


@router.get("/history")
async def get_query_history(
    current_user: TokenData = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get user's query history"""
    # TODO: Implement history retrieval
    return {"history": []}
