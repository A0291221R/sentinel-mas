"""
Admin Routes

Admin-only endpoints requiring elevated privileges.
"""

import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends

from ..auth import AuthContext, TokenData, require_role
from ..models import QueryRequest, QueryResponse
from ..services.sentinel_service import SentinelService, get_sentinel_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/queries", response_model=QueryResponse)
async def admin_query(
    request: QueryRequest,
    current_user: TokenData = Depends(require_role("admin", "supervisor")),
    sentinel_service: SentinelService = Depends(get_sentinel_service),
) -> QueryResponse:
    """
    Admin-only query endpoint

    Same as regular query endpoint but requires admin or supervisor role.
    Could have different rate limits, priority, or features.

    Requires JWT token with 'admin' or 'supervisor' role.

    Args:
        request: QueryRequest with prompt
        current_user: Must have admin/supervisor role
        sentinel_service: Injected service

    Returns:
        QueryResponse with output

    Raises:
        403 Forbidden: If user doesn't have required role
    """
    auth_context = AuthContext(
        user_id=current_user.user_id,
        user_role=current_user.user_role,
        email=current_user.email,
        session_id=f"admin-{uuid.uuid4().hex[:10]}",
        request_id=f"req-{uuid.uuid4().hex[:10]}",
    )

    result = await sentinel_service.process_query(
        prompt=request.prompt,
        auth_context=auth_context,
        options=request.options,
        context=request.context,
    )

    return QueryResponse(**result)


@router.get("/config")
async def get_config_info(
    current_user: TokenData = Depends(require_role("admin")),
) -> Dict[str, Any]:
    """
    Get configuration information (admin only)

    Returns safe configuration info for debugging.
    Only accessible to users with 'admin' role.

    Args:
        current_user: Must have admin role

    Returns:
        Dict with config info

    Example Response:
        {
            "sentinel_model": "gpt-4o-mini",
            "recursion_limit": 15,
            "central_url": "http://localhost:8000"
        }
    """
    sentinel_service = get_sentinel_service()
    return sentinel_service.get_config_info()
