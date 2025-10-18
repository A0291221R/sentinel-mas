from datetime import datetime
import pytz
from langchain_core.messages import HumanMessage

SGT = pytz.timezone("Asia/Singapore")

def last_user_text(messages):
    for m in reversed(messages or []):
        if isinstance(m, HumanMessage):
            return m.content or ""
    return ""

def ms_to_sgt(ms: int | None):
    if ms is None: return None
    return datetime.fromtimestamp(int(ms)/1000, SGT).strftime("%Y-%m-%d %H:%M:%S %Z")
