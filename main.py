import getpass
import time
import uuid

from langchain_core.messages import HumanMessage

from sentinel_mas.agents.crew_agents import State

# from sentinel_mas.agents.crew_with_guard import CreateCrew
from sentinel_mas.agents.crew_with_guard import CreateCrew

# from sentinel_mas.memory.session_store import append_user
from sentinel_mas.policy_sentinel.runtime import context_scope

app = CreateCrew()

# # # Print workflow
# png_bytes = app.get_graph().draw_mermaid_png()           # returns PNG bytes
# with open("sentinel_flow.png", "wb") as f:
#     f.write(png_bytes)

if __name__ == "__main__":

    # 1) Boot runtime (loads @tool modules, validates policy allowlist)
    # start_runtime(with_metrics=False)   # keep False; you’ll add Prom later

    # 2) Basic session context (persist for the whole CLI session)
    session_id = f"cli-{uuid.uuid4().hex[:10]}"
    user_id = getpass.getuser() or "cli_user"
    user_role = "supervisor"  # change to "supervisor"/"admin" when needed

    state = {
        "messages": [],
        "user_question": "",
        # Optional router seed; PolicyExecutor can also derive route later
        # "route": "SOP",
        "user_id": user_id,
        "user_role": user_role,
        "session_id": session_id,
    }

    while True:
        try:
            user_input = input("query: ").strip()

        except (EOFError, KeyboardInterrupt):
            print("Opps...Bye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("Bye!")
            break

        # 3) Per-request context
        state["user_question"] = user_input
        state["request_id"] = f"req-{uuid.uuid4().hex[:10]}"  # new ID each turn

        t0 = time.perf_counter()

        result = app.invoke(state)
        print(f"Elapsed Time: {(time.perf_counter() - t0) : .2f}s")
        print(result["messages"][-1].content)
