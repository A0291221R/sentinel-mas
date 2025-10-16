from __future__ import annotations
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

import yaml
from jinja2 import Template
from pydantic import BaseModel, Field, ValidationError
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

# ---------- Optional: import your unified state type ----------
try:
    # If you've defined SentinelState elsewhere, this keeps type hints nice.
    from crew_agents import State as SentinelState  # noqa: F401
except Exception:
    SentinelState = Dict[str, Any]  # fallback for typing only


# ---------- Agents bundle ----------
@dataclass(frozen=True)
class AgentsBundle:
    faq_agent: Any        # CrewAgent
    tracking_agent: Any   # CrewAgent


# ---------- Route decision schema ----------
class RouteDecision(BaseModel):
    route: str = Field(pattern=r"^(SOP|INSIGHT|TRACKING)$")
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


# ---------- Heuristic patterns (fast path) ----------
ROUTE_KEYWORDS: Dict[str, list[str]] = {
    "SOP": [
        r"\bsop\b", r"\bprocedure\b", r"\bhow do i\b", r"\bsteps?\b", r"\bescalat",
        r"\bpolicy\b", r"\brestart\b", r"\brecover(y|ies)\b", r"\bincident\b",
        r"\balert handling\b"
    ],
    "INSIGHT": [
        r"\binsight\b", r"\bresearch\b", r"\bwhat'?s new\b", r"\blatest\b", r"\bcompare\b",
        r"\bpros?\s*/\s*cons?\b", r"\btrend\b", r"\bbenchmark\b", r"\bliterature\b"
    ],
    "TRACKING": [
        r"\btrack(_id| id| uid)\b", r"\bsession(s)?\b", r"\bidentity\b", r"\bid[- ]fusion\b",
        r"\b(par|attribute)s?\b", r"\bmovement update\b", r"\bquery\b", r"\breid\b",
        r"\btop[- ]k\b"
    ],
}


def _heuristic_route(user_q: str) -> Optional[str]:
    q = user_q.lower()
    # tie-breaker priority: SOP > TRACKING > INSIGHT
    for route in ("SOP", "TRACKING", "INSIGHT"):
        if any(re.search(p, q) for p in ROUTE_KEYWORDS[route]):
            return route
    return None


# ---------- Router class ----------
class Router:
    """
    Stateless-ish router: decide route (heuristic -> LLM fallback), write `router_decision`,
    and dispatch to the corresponding CrewAgent with the SAME state.
    """

    def __init__(
        self,
        agents: AgentsBundle,
        router_yaml_path: str | Path = "prompts/router.yaml",
        llm: Optional[ChatOpenAI] = None,
    ):
        self.agents = agents
        self.router_yaml_path = Path(router_yaml_path)
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # preload template (keeps runtime lean)
        data = yaml.safe_load(self.router_yaml_path.read_text(encoding="utf-8")) or {}
        self._router_template = Template(data.get("template", ""))

    # ---- public surface -----------------------------------------------------

    def route(self, user_question: str) -> RouteDecision:
        """Return a RouteDecision using heuristic first, LLM fallback if needed."""
        route = _heuristic_route(user_question)
        if route:
            return RouteDecision(route=route, confidence=0.8, reason="Heuristic match")

        rendered = self._router_template.render(user_question=user_question)
        msg = self.llm.invoke([SystemMessage(content=rendered)])
        try:
            raw = json.loads(msg.content)
            return RouteDecision(**raw)
        except (json.JSONDecodeError, ValidationError):
            # ultra-defensive default
            return RouteDecision(route="SOP", confidence=0.3, reason="Fallback default")

    def dispatch(self, state: SentinelState) -> SentinelState:
        """
        Mutates & returns state:
          - sets state['router_decision']
          - calls the appropriate CrewAgent
        """
        user_q = state.get("user_question", "")
        if not user_q:
            raise ValueError("router: missing `user_question` in state")

        decision = self.route(user_q)
        state["router_decision"] = decision.model_dump()

        if decision.route == "SOP":
            state.setdefault("sop_context", None)          # optional: prefill via retriever
            return self.agents.faq_agent(state)

        # TRACKING
        state.setdefault("ops_context", None)              # optional: prefill via retriever
        return self.agents.tracking_agent(state)


# ---------- convenience factory ----------
def create_default_router(
    faq_agent: Any,
    tracking_agent: Any,
    router_yaml_path: str | Path = "prompts/router.yaml",
    model: str = "gpt-4o-mini",
) -> Router:
    agents = AgentsBundle(faq_agent=faq_agent, tracking_agent=tracking_agent)
    llm = ChatOpenAI(model=model, temperature=0)
    return Router(agents=agents, router_yaml_path=router_yaml_path, llm=llm)
