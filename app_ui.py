from __future__ import annotations
import os
import gradio as gr
from typing import Dict, Any, List, Tuple

from sentinel_mas.crew import CreateCrew   # your graph factory
from sentinel_mas.crew_agents import State # your MessagesState subclass
from langchain_core.messages import HumanMessage, AIMessage

# --- Build the graph once (global)
GRAPH = CreateCrew()

# --- Helpers ---------------------------------------------------------------
def _init_state() -> Dict[str, Any]:
    # Your State requires at least messages + user_question (filled per-turn)
    return {"messages": []}

def _history_to_messages(history: List[Tuple[str, str]]) -> List:
    """Convert Gradio history → LangChain messages (Human/AI)."""
    msgs = []
    for user, bot in history:
        if user:
            msgs.append(HumanMessage(content=user))
        if bot:
            msgs.append(AIMessage(content=bot, name="assistant"))
    return msgs

def _extract_last_ai(state: Dict[str, Any]) -> str:
    for m in reversed(state.get("messages", [])):
        if isinstance(m, AIMessage):
            return m.content or ""
    return "(no response)"

# --- Core chat fn ----------------------------------------------------------
def chat_turn(user_text: str, chat_history: List[Tuple[str, str]], state: Dict[str, Any], show_debug: bool):
    """
    Gradio expects:
      inputs: (user_text, chat_history, state, show_debug)
      outputs: (chat_history, state, router_json)
    """
    # 1) Sync Gradio history → LC messages, append new Human message
    msgs = _history_to_messages(chat_history)
    msgs.append(HumanMessage(content=user_text))

    # 2) Build LangGraph state
    lg_state: State = {
        "messages": msgs,
        "user_question": user_text,  # router + agents use this
    }

    # 3) Invoke graph
    out_state: Dict[str, Any] = GRAPH.invoke(lg_state)
    subset = {
        "route": out_state.get("route") or out_state.get("router_decision"),
        "start_ms": out_state.get("start_ms"),
        "end_ms": out_state.get("end_ms"),
        "time_label": out_state.get("time_label"),
    }

    # 4) Read assistant reply
    reply = _extract_last_ai(out_state)

    # 5) Update Gradio chat history
    chat_history = chat_history + [(user_text, reply)]

    # 6) Router debug (optional)
    router_info = out_state.get("router_decision", None) if show_debug else None

    # 7) Keep full state around between turns
    return chat_history, out_state, router_info, subset

def clear_session():
    return [], _init_state(), None

# --- UI --------------------------------------------------------------------
with gr.Blocks(fill_height=True, title="Sentinel Assistant") as demo:
    gr.Markdown("## 🛰️ Sentinel Assistant\nAsk SOP, CCTV events, or send Tracking commands.")
    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(height=520, type="tuples", show_copy_button=True)
            with gr.Row():
                txt = gr.Textbox(
                    placeholder="Type your question… (e.g., Who entered Building-A between 14:00–16:00?)",
                    scale=5,
                    autofocus=True,
                    container=True,
                    lines=1,
                )
                send = gr.Button("Send", variant="primary", scale=1)
            with gr.Row():
                clear = gr.Button("Clear", variant="secondary")
        with gr.Column(scale=2):
            show_debug = gr.Checkbox(label="Show router decision", value=False)
            router_json = gr.JSON(label="Router decision", value=None)

    # hidden session state
    session_state = gr.State(_init_state())

    # Wire events
    send.click(
        chat_turn,
        inputs=[txt, chatbot, session_state, show_debug],
        outputs=[chatbot, session_state, router_json],
    )
    txt.submit(
        chat_turn,
        inputs=[txt, chatbot, session_state, show_debug],
        outputs=[chatbot, session_state, router_json],
    )
    clear.click(
        clear_session,
        inputs=None,
        outputs=[chatbot, session_state, router_json],
    )

if __name__ == "__main__":
    # Gradio runner
    demo.queue(default_concurrency_limit=8, max_size=64).launch(
        server_name=os.getenv("HOST", "localhost"),
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
        inbrowser=False,
        show_error=True,
    )
