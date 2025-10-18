from __future__ import annotations
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage

# from sentinel_mas.tools import get_tracks
from sentinel_mas.timewin import resolve_time_window
from sentinel_mas.tools.sop_tools import get_sop, search_sop
from sentinel_mas.tools.events_tools import list_anomaly_event, who_entered_zone
from sentinel_mas.tools.tracking_tools import send_track, send_cancel, get_track_status, get_person_insight

# Policy Sentinel
from sentinel_mas.policy_sentinel.executor import PolicyExecutor


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
event_tool_node= PolicyExecutor(route="EVENTS", tools=event_tools, single_call=True, freeze_time_window=True)
faq_tool_node = PolicyExecutor(route="SOP", tools=faq_tools, single_call=True, freeze_time_window=True)
tracking_tool_node = PolicyExecutor(route="TRACKING", tools=tracking_tools, single_call=True, freeze_time_window=True)

# router_tool_node = ToolNode(router_tools)



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

def register_agent_and_tools(graph: StateGraph, agent_name: str, agent_node, tool_node, end_node = END):
    tools_name = f"{agent_name}_tools"
    
    graph.add_node(agent_name, agent_node)
    graph.add_node(tools_name, tool_node)
    graph.add_conditional_edges(
        agent_name, tools_condition,
        {"tools": tools_name, END: end_node}
    )
    graph.add_edge(tools_name, agent_name)
    return graph
    

def CreateCrew():
    graph = StateGraph(State)

    graph = register_agent_and_tools(graph, "faq_agent", faq_agent, faq_tool_node)
    graph = register_agent_and_tools(graph, "events_agent", events_agent, event_tool_node)
    graph = register_agent_and_tools(graph, "tracking_agent", tracking_agent, tracking_tool_node)


    graph.add_node("router_agent", router_agent)
    graph.add_node("parse_time_node", parse_time_node)


    graph.set_entry_point("router_agent")
    graph.add_conditional_edges(
        "router_agent", router_condition,
        {
            "SOP": "faq_agent", 
            "EVENTS": "parse_time_node", 
            "TRACKING": "tracking_agent", 
            END: END
        }
    )
    graph.add_edge("parse_time_node", "events_agent")

    for agent_name in ['faq_agent', 'events_agent', 'tracking_agent']:
        graph.add_edge(agent_name, END)

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
