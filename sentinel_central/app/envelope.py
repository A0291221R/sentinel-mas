from typing import Any, Dict, Literal
from pydantic import BaseModel
from time import time

class Envelope(BaseModel):
    type: Literal['par-event','ad-event','tts-event','movement-update','anomaly-alert']
    version: int = 1
    ts_ms: int
    created_by: str
    payload: Dict[str, Any]

def now_ms() -> int:
    return int(time() * 1000)

def pack_event(event_type: Envelope.__annotations__['type'],
               payload: Dict[str, Any],
               created_by: str,
               version: int = 1) -> Dict[str, Any]:
    env = Envelope(type=event_type, version=version, ts_ms=now_ms(), created_by=created_by, payload=payload)
    return env.model_dump()
