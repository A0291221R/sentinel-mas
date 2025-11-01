import getpass
import time
import uuid

from sentinel_mas.agents.crew import CreateCrew

# from sentinel_mas.agents.crew_agents import State
# from sentinel_mas.config import OPENAI_API_KEY, OPENAI_MODEL

sop_questions = [
    "How do I escalate a Level-2 anomaly alert? What’s the deadline and who to notify?",
    "What are the exact steps to safely restart Edge-Sentinel on a field device?",
    "How do I acknowledge an alert and mark it as False Positive with a note?",
    "Central dashboard is down—what’s the outage procedure and update cadence?",
    "How do I assign an identity to a new track,and when should I escalate for review?",
    "User can’t pass MFA—what’s the SOP for login recovery?",
    "What’s the process for data deletion under the retention policy?",
    "Who approves identity merges and what evidence/scores must be checked?",
]


app = CreateCrew()

# # # # Print workflow
# png_bytes = app.get_graph().draw_mermaid_png()           # returns PNG bytes
# with open("sentinel_flow.png", "wb") as f:
#     f.write(png_bytes)

if __name__ == "__main__":

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

        # state['messages'].append(HumanMessage(content=user_input))
        state["user_question"] = user_input
        t0 = time.perf_counter()
        result = app.invoke(state)
        print(f"Elapsed Time: {(time.perf_counter() - t0) : .2f}s")
        print(result["messages"][-1].content)
