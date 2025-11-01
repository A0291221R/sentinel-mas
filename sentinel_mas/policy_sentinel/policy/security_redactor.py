import threading
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml


class SecurityRedactor:
    """Handles loading security policy and redacting sensitive fields."""

    def __init__(self, policy_path: Union[str, Path]):
        self._path = Path(policy_path)
        self._lock = threading.RLock()
        self.reload_policy()

    def reload_policy(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(f"Missing security policy file: {self._path}")
        with open(self._path, "r", encoding="utf-8") as f:
            policy = yaml.safe_load(f) or {}
        redaction = policy.get("redaction", {})
        with self._lock:
            self._keys = {k.lower() for k in redaction.get("keys", [])}
            self._depth = int(redaction.get("max_depth", 3))

    def redact_args(
        self, args: Optional[Dict[str, Any]], _level: int = 0
    ) -> Union[Dict[str, Any], str]:
        if args is None:
            return {}
        if _level > self._depth:
            return "<...>"

        redacted: dict[str, Any] = {}
        for k, v in args.items():
            k_lower = k.lower()
            if k_lower in self._keys or any(sub in k_lower for sub in self._keys):
                redacted[k] = "<REDACTED>"
            elif isinstance(v, dict):
                redacted[k] = self.redact_args(v, _level + 1)
            elif isinstance(v, list):
                redacted[k] = [
                    (
                        self.redact_args(i, _level + 1)
                        if isinstance(i, dict)
                        else self._truncate(i)
                    )
                    for i in v
                ]
            else:
                redacted[k] = self._truncate(v)
        return redacted

    @staticmethod
    def _truncate(v: Any) -> Any:
        return v[:30] + "...(truncated)" if isinstance(v, str) and len(v) > 100 else v
