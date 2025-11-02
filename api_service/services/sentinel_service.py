"""
Sentinel Service

Service layer that wraps the sentinel_mas package for API use.
This is the bridge between the API and the MAS package.
"""

import time
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

# Import from sentinel_mas package
from sentinel_mas import CreateCrew
from sentinel_mas import get_config as get_sentinel_config

from ..auth import AuthContext
from ..config import get_api_config

api_config = get_api_config()
sentinel_config = get_sentinel_config()


class SentinelService:
    """
    Service layer for Sentinel MAS operations

    This class wraps the sentinel_mas package and provides
    API-friendly methods for processing queries.
    """

    def __init__(self) -> None:
        """
        Initialize with sentinel_mas CreateCrew

        Creates the crew instance and loads configuration.
        """
        self.crew = CreateCrew()
        self.recursion_limit = sentinel_config.RECURSION_LIMIT

    async def process_query(
        self,
        prompt: str,
        auth_context: AuthContext,
        options: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process a user query using the sentinel_mas package

        This is the main method that:
        1. Takes user input and auth context
        2. Builds state for sentinel_mas
        3. Calls the MAS package
        4. Returns formatted response

        Args:
            prompt: User query string (e.g., "How do I set tracking?")
            auth_context: Authenticated user context (from JWT)
            options: Optional query processing options
            context: Optional additional context

        Returns:
            Dict with:
                - output: The response from Sentinel MAS
                - session_id: Session identifier
                - request_id: Request identifier
                - elapsed_time: Processing time in seconds
                - model_used: Which model was used

        Raises:
            HTTPException: If processing fails

        Example:
            result = await service.process_query(
                prompt="How to set tracking?",
                auth_context=auth_context
            )
            # Returns: {
            #     "output": "To set tracking...",
            #     "session_id": "api-abc123",
            #     "request_id": "req-xyz789",
            #     "elapsed_time": 2.45
            # }
        """
        prompt = prompt.strip()
        if len(prompt) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalida query param",
            )

        # Build state for sentinel_mas
        # This is what gets passed to the MAS package
        state: Dict[str, Any] = {
            "messages": [],  # Conversation history
            "user_question": prompt,  # The actual question
            "user_id": auth_context.user_id,  # Who's asking
            "user_role": auth_context.user_role,  # Their role
            "session_id": auth_context.session_id,  # Session tracking
            "request_id": auth_context.request_id,  # Request tracking
        }

        # Add optional fields if provided
        if options:
            state["options"] = options
        if context:
            state["context"] = context

        # Start timing
        t0 = time.perf_counter()

        try:
            # Call sentinel_mas package
            result = await self.crew.ainvoke(
                state, config={"recursion_limit": self.recursion_limit}
            )

            # Calculate elapsed time
            elapsed_time = time.perf_counter() - t0

            # Return formatted response
            return {
                "output": result["messages"][-1].content,
                "session_id": auth_context.session_id,
                "request_id": auth_context.request_id,
                "elapsed_time": elapsed_time,
                "model_used": sentinel_config.OPENAI_MODEL,
            }

        except Exception as e:
            # Log error and return HTTP error
            print(f"Error processing query: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing query: {str(e)}",
            )

    def get_config_info(self) -> Dict[str, Any]:
        """
        Get configuration information for debugging

        Returns basic config info (safe for admin users)

        Returns:
            Dict with config information
        """
        return {
            "sentinel_model": sentinel_config.OPENAI_MODEL,
            "recursion_limit": self.recursion_limit,
            "central_url": sentinel_config.SENTINEL_CENTRAL_URL,
        }


# Singleton instance
# Only one instance of the service is created and reused
_service: Optional[SentinelService] = None


def get_sentinel_service() -> SentinelService:
    """
    Get or create SentinelService singleton

    This ensures only one instance of the service exists.
    Used as a FastAPI dependency.

    Returns:
        SentinelService: The singleton service instance
    """
    global _service
    if _service is None:
        _service = SentinelService()
    return _service
