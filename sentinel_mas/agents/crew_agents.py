from __future__ import annotations

import json

# ---------- Graph State (new reducer style) ----------
from typing import Any, Dict

from jinja2 import Template
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from sentinel_mas.agents import AGENT_REGISTRY
from sentinel_mas.config import Config
from sentinel_mas.state.graph_state import GraphState as State

# class State(MessagesState):
#     user_question: str

#     # pre-parsed time window (optional)
#     start_ms: NotRequired[int]
#     end_ms: NotRequired[int]
#     time_label: NotRequired[str]

#     # handy optional filters
#     location_id: NotRequired[str]
#     camera_id: NotRequired[str]

#     # routing
#     route: NotRequired[str]
#     router_decision: NotRequired[Dict[str, Any]]

#     # audit / identity metadata
#     user_id: NotRequired[str]
#     user_role: NotRequired[Literal["viewer","operator","supervisor","admin"]]
#     session_id: NotRequired[str]     # stable across a CLI/app session
#     request_id: NotRequired[str]     # new per user turn

# print(f"API key: {Config.OPENAI_API_KEY}")


# ---------- Callable node ----------
class CrewAgent:
    """
    Callable LangGraph node that renders a system prompt from YAML
    and can call bound tools via tool calls.
    """

    def __init__(
        self,
        agent_name: str,
    ):
        self.name = agent_name
        self.runtime = AGENT_REGISTRY[agent_name]
        base = ChatOpenAI(
            api_key=lambda: Config.OPENAI_API_KEY,
            model=self.runtime.llm_model,
            temperature=self.runtime.llm_temperature,
            max_completion_tokens=self.runtime.llm_max_tokens,
        )
        self.tools = list(self.runtime.tools.values())
        self.llm = base.bind_tools(self.tools) if self.tools else base

    def build_messages(self, state: State) -> list[BaseMessage]:
        sys_text = Template(self.runtime.system_prompt).render(
            **{k: v for k, v in state.items() if k != "messages"}
        )
        return [SystemMessage(content=sys_text), *state["messages"]]

    def __call__(self, state: State) -> Dict[str, Any]:
        msgs = self.build_messages(state)
        # DO NOT sanitize; LangChain handles pairing internally

        print(
            f"\n[AGENT {self.name}] IN messages={len(msgs)} "
            f"start_ms={state.get('start_ms')} end_ms={state.get('end_ms')} \
            time_label={state.get('time_label')}"
        )
        # print(f"state: {state}\n")
        try:
            resp = self.llm.invoke(msgs)  # AIMessage (may include tool_calls)

        except Exception as e:
            print(f"[AGENT {self.name}] ERROR:", type(e).__name__, e)
            raise

        tcalls = getattr(resp, "tool_calls", None)
        if tcalls:

            print(
                f"[AGENT {self.name}] tool_calls:",
                json.dumps(tcalls, ensure_ascii=False),
            )

        # Keep the original AIMessage; just tag the name for traceability
        if isinstance(resp, AIMessage):
            resp.name = self.name
            return {"messages": [resp]}
        else:
            ai = AIMessage(content=str(resp), name=self.name)
            return {"messages": [ai]}
