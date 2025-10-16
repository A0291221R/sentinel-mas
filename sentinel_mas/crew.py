from __future__ import annotations
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage

# from sentinel_mas.tools import get_tracks
from sentinel_mas.timewin import resolve_time_window
from sentinel_mas.tools.sop_tools import get_sop, search_sop
from sentinel_mas.tools.cctv_events_tools import list_anomaly_event, who_entered_zone
from sentinel_mas.tools.tracking_control_tools import send_track, send_cancel, get_track_status, get_person_insight

from .crew_agents import State, CrewAgent
from config import OPENAI_API_KEY, OPENAI_MODEL

# ~~~ Per-agent tool permissions ~~~
router_tools =[]
faq_tools = [get_sop, search_sop]
event_tools = [list_anomaly_event, who_entered_zone]
tracking_tools = [send_track, send_cancel, get_track_status, get_person_insight]

#~~~ Agents ~~~
router_agent   = CrewAgent("router_agent", "router.yaml", tools=router_tools, temperature=0.00, max_tokens=120)
faq_agent      = CrewAgent("faq_agent", "faq_sop.yaml", tools=faq_tools, temperature=0.05, max_tokens=350)
events_agent   = CrewAgent("events_agent", "cctv_events.yaml", tools=event_tools, temperature=0.05, max_tokens=1300)
tracking_agent = CrewAgent("tracking_agent", "tracking_ops.yaml", tools=tracking_tools, temperature=0.05, max_tokens=300)

#~~~ ToolNodes for each agent
event_tool_node = ToolNode(event_tools)
router_tool_node = ToolNode(router_tools)
faq_tool_node = ToolNode(faq_tools)
tracking_tool_node = ToolNode(tracking_tools)


def parse_time_node(state):
    if state.get("start_ms") and state.get("end_ms"):
        return state  # already provided elsewhere
    q = state.get("user_question", "") or ""
    try:
        start_ms, end_ms, label = resolve_time_window(q)
        print(f"parsed time: start_ms:{start_ms}, end_ms:{end_ms}, label:{label}")
        return {"start_ms": start_ms, "end_ms": end_ms, "time_label": label}
    except Exception as e:
        # leave unset; EVENTS agent will ask for one field if needed
        print("[PARSE] failed:", e)
        return {}

def register_agent_and_tools(graph: StateGraph, agent: str, tools: str):
    graph.add_node(agent, tracking_agent)
    graph.add_node(tools, tracking_tool_node)
    graph.add_conditional_edges(
        agent, tools_condition,
        {"tools": tools, END: END}
    )
    graph.add_edge(tools, agent)
    return graph
    

def CreateCrew():
    graph = StateGraph(State)

    # Graph nodes:
    # wiring faq agent node & tools
    graph.add_node("faq_agent", faq_agent)
    graph.add_node("faq_tool_node", faq_tool_node)
    graph.add_conditional_edges(
        "faq_agent", tools_condition,
        {"tools": "faq_tool_node", END: END}
    )
    graph.add_edge("faq_tool_node", "faq_agent")

    # wiring event agent node & tools
    graph.add_node("parse_time_node", parse_time_node)
    graph.add_node("events_agent", events_agent)
    graph.add_node("event_tool_node", event_tool_node)
   
    graph.add_edge("parse_time_node", "events_agent")
    graph.add_conditional_edges(
        "events_agent", tools_condition,
        {"tools": "event_tool_node", END: END}
    )
    graph.add_edge("event_tool_node", "events_agent")

    # wiring tracking agent node & tools
    graph.add_node("tracking_agent", tracking_agent)
    graph.add_node("tracking_tool_node", tracking_tool_node)
    graph.add_conditional_edges(
        "tracking_agent", tools_condition,
        {"tools": "tracking_tool_node", END: END}
    )
    graph.add_edge("tracking_tool_node", "tracking_agent")

    # wiring rouer and route condition:
    graph.set_entry_point("router_agent")
    graph.add_node("router_agent", router_agent)
    graph.add_conditional_edges(
        "router_agent", router_condition,
        {
            "SOP": "faq_agent", 
            "EVENTS": "parse_time_node", 
            "TRACKING": "tracking_agent", 
            END: END
        }
    )

    for agent_name in ['faq_agent', 'events_agent', 'tracking_agent']:
        graph.set_finish_point(agent_name)

    return graph.compile()


import json
from langchain_core.messages import AIMessage

def router_condition(state) -> str:
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
        payload = json.loads(ai.content)
        route = payload.get("route", "").upper().strip()
        if route in {"SOP", "EVENTS", "TRACKING"}:
            # optionally persist the router decision for audit
            state["router_decision"] = payload
            return route
    except Exception:
        pass

    return END
