from __future__ import annotations

import json
from typing import Any, Dict

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import tools_condition

from sentinel_mas.agents.crew_agents import CrewAgent, State

# from sentinel_mas.tools import get_tracks
# Policy Sentinel
from sentinel_mas.policy_sentinel.secure_tool_node import SecureToolNode
from sentinel_mas.timewin import resolve_time_window
from sentinel_mas.tools.events_tools import list_anomaly_event, who_entered_zone
from sentinel_mas.tools.sop_tools import get_sop, search_sop
from sentinel_mas.tools.tracking_tools import (
    get_person_insight,
    get_track_status,
    send_cancel,
    send_track,
)

# ~~~ Per-agent tool permissions ~~~
# router_tools = []
faq_tools = [get_sop, search_sop]
event_tools = [list_anomaly_event, who_entered_zone]
tracking_tools = [send_track, send_cancel, get_track_status, get_person_insight]

# ~~~ Agents ~~~
router_agent = CrewAgent("router_agent")
faq_agent = CrewAgent("faq_agent")
events_agent = CrewAgent("events_agent")
tracking_agent = CrewAgent("tracking_agent")

# ~~~ ToolNodes for each agent
event_tool_node = SecureToolNode(
    route="EVENTS", tools=event_tools, freeze_time_window=True
)
faq_tool_node = SecureToolNode(route="SOP", tools=faq_tools, freeze_time_window=True)
tracking_tool_node = SecureToolNode(
    route="TRACKING", tools=tracking_tools, freeze_time_window=True
)

# router_tool_node = ToolNode(router_tools)


def parse_time_node(state: State) -> State:
    if state.get("start_ms") and state.get("end_ms"):
        return state  # already provided elsewhere
    q = state.get("user_question", "") or ""
    try:
        start_ms, end_ms, label = resolve_time_window(q)
        print(f"parsed time: start_ms:{start_ms}, end_ms:{end_ms}, label:{label}")
        # state['start_ms'] = start_ms
        # state['end_ms'] = end_ms
        return {**state, "start_ms": start_ms, "end_ms": end_ms, "time_label": label}
    except Exception as e:
        # leave unset; EVENTS agent will ask for one field if needed
        print("[PARSE] failed:", e)
        return {**state}


def post_tool_router(state: State) -> str:
    # We decide next step based on what SecureToolNode just did
    # print(f"[POST_TOOL_ROUTER] halt: {state}")
    if state.get("halt", False):
        return "HALT"
    return "CONTINUE"


def finalize_error_node(state: State) -> Dict[str, Any]:
    """
    Turn the last ToolMessage error into a final answer for the user.
    No more tool calls. No retry.
    """
    # Find the last tool message
    tool_msg = next(
        (m for m in reversed(state["messages"]) if isinstance(m, ToolMessage)), None
    )

    user_friendly = "An internal error occurred."
    if tool_msg:
        try:
            raw = tool_msg.content
            if isinstance(raw, str):
                payload: Any = json.loads(raw)
            else:
                payload = raw  # already a list/dict; skip decoding

            if isinstance(raw, str):
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as e:
                    print(f"failed to decode JSON: {e}")
                    payload = {"error": str(e)}
            else:
                payload = raw  # already a dict or list; no need to decode

            if payload.get("status") == "DENIED":
                user_friendly = (
                    payload.get("msg")
                    or """Access denied. You are not allowed \
                        to retrieve that information."""
                )
            elif payload.get("status") == "ERROR":
                user_friendly = (
                    payload.get("msg")
                    or """The request could not be completed due \
                        to an internal error."""
                )
        except Exception:
            pass

    assistant_msg = AIMessage(
        content=user_friendly,
        name="system",
    )

    return {
        **state,
        "messages": state["messages"] + [assistant_msg],
    }


def register_agent_and_tools(
    graph: StateGraph,
    agent_name: str,
    agent_node: CrewAgent,
    tool_node: Any,
    end_node: str = END,
    error_node: str = "finalize_error_node",
) -> StateGraph:
    tools_name = f"{agent_name}_tools"

    graph.add_node(agent_name, agent_node)
    graph.add_node(tools_name, tool_node)
    graph.add_conditional_edges(
        agent_name, tools_condition, {"tools": tools_name, END: end_node}
    )
    graph.add_conditional_edges(
        tools_name, post_tool_router, {"CONTINUE": agent_name, "HALT": error_node}
    )
    # graph.add_edge(tools_name, agent_name)
    return graph


def CreateCrew() -> Any:
    graph = StateGraph(State)

    graph.add_node("finalize_error_node", finalize_error_node)
    graph.add_node("parse_time_node", parse_time_node)

    graph = register_agent_and_tools(graph, "faq_agent", faq_agent, faq_tool_node)
    graph = register_agent_and_tools(
        graph, "events_agent", events_agent, event_tool_node
    )
    graph = register_agent_and_tools(
        graph, "tracking_agent", tracking_agent, tracking_tool_node
    )

    graph.add_node("router_agent", router_agent)

    graph.set_entry_point("router_agent")
    graph.add_conditional_edges(
        "router_agent",
        router_condition,
        {
            "SOP": "faq_agent",
            "EVENTS": "parse_time_node",
            "TRACKING": "tracking_agent",
            END: END,
        },
    )
    graph.add_edge("parse_time_node", "events_agent")

    for agent_name in [
        "faq_agent",
        "events_agent",
        "tracking_agent",
        "finalize_error_node",
    ]:
        graph.add_edge(agent_name, END)
    return graph.compile()


def router_condition(state: State) -> str:
    """
    Reads the last AIMessage from router_agent, expects JSON:
      {"route":"SOP|DB|TRACKING","confidence":0.xx,"reason":"..."}
    Returns the route string to choose the next node.
    """
    msgs = state["messages"]
    # find the last AI message (router output)
    ai = next((m for m in reversed(msgs) if isinstance(m, AIMessage)), None)
    if ai is None:
        return END  # or raise

    try:
        raw = ai.content
        if isinstance(raw, str):
            payload: Any = json.loads(raw)
        else:
            payload = raw  # already a list/dict; skip decoding
        route: str = payload.get("route", "").upper().strip()
        if route in {"SOP", "EVENTS", "TRACKING"}:
            # optionally persist the router decision for audit
            state["route"] = route
            state["router_decision"] = payload
            print(f'route has been set to "{route}"')
            # set_graph_state(state)
            return route
    except Exception:
        pass

    return END
