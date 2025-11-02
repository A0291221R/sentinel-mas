"""
Sentinel MAS Package

A Multi-Agent System for intelligent task processing.

Usage:
    from sentinel_mas import CreateCrew, get_config

    crew = CreateCrew()
    config = get_config()
"""

__version__ = "0.1.0"

from .agents.crew_with_guard import CreateCrew
from .config import SentinelMASConfig, get_config

__all__ = [
    "CreateCrew",
    "get_config",
    "SentinelMASConfig",
    "__version__",
]
