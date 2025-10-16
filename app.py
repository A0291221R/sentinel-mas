from langchain_core.messages import HumanMessage
from config import OPENAI_API_KEY, OPENAI_MODEL
from sentinel_mas.crew import CreateCrew
from sentinel_mas.crew_agents import State
from langsmith import Client, tracing_context

import time

sop_questions = [
	"How do I escalate a Level-2 anomaly alert? What’s the deadline and who to notify?",
	"What are the exact steps to safely restart Edge-Sentinel on a field device?",
	"How do I acknowledge an alert and mark it as False Positive with a note?",
	"Central dashboard is down—what’s the outage procedure and update cadence?",
	"How do I assign an identity to a new track, and when should I escalate for review?",
	"User can’t pass MFA—what’s the SOP for login recovery?",
	"What’s the process for data deletion under the retention policy?",
	"Who approves identity merges and what evidence/scores must be checked?"
]


app = CreateCrew()

# # # # Print workflow
# png_bytes = app.get_graph().draw_mermaid_png()           # returns PNG bytes
# with open("sentinel_flow.png", "wb") as f:
#     f.write(png_bytes)

if __name__ == "__main__":
    # db retrieval
    # init_state: State = {
    #     "messages": [],
    #     "user_question": "Show me the last 10 sessions on camera CAM-05 today.",
    #     "db_context": "tables: sessions, tracks, par_events; sessions(start_ms,end_ms,camera_id,session_id)"
    # }

    # faq SOP
    # init_state = {
    #     "messages": [],
    #     "user_question": "Operator guidance for handling abnormal crowd behavior alerts?",
    #     "sop_context": "- [2.4.5] Anomaly Alert Handling: verify on dashboard, acknowledge, start escalation if severity ≥ MED.",
    # }

    # # tracking
    # init_state = {
    #     "messages": [],
    #     "user_question": "set track to target with identity ID 1234",
    #     "ops_context": "",
    # }

    # init_state = {
    #     "messages": [],
    #     "user_question": "List movement updates for CAM-05 in the last 15 minutes and highlight new track_uids.",
    #     "ops_context": "- movement_update table (t_ms, camera_id, track_uid, x,y,w,h); limit 50; order by t_ms desc.",
    # }
    state = {
        "messages": [],
        "user_question": ""
    }

    while True:
        try:
            user_input = input('query: ').strip()
            
        except (EOFError, KeyboardInterrupt):
            print('Opps...Bye!')
            break

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit']:
            print('Bye!')
            break
        
        # state['messages'].append(HumanMessage(content=user_input))
        state['user_question'] = user_input
        t0 = time.perf_counter()
        result = app.invoke(state)
        print(f'Elapsed Time: {(time.perf_counter() - t0) : .2f}s')
        print(result["messages"][-1].content)