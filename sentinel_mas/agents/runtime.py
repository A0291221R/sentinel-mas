from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Any, List

@dataclass
class AgentRuntime:
    name: str
    system_prompt: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int
    tools: Dict[str, Callable[..., Any]]
