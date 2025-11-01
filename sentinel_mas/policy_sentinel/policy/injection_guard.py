from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


class InjectionGuard:
    """
    Rule-based prompt-injection / jailbreak / abuse detector.

    Usage (per tool call):
        allowed, reason = guard.scan_single(
            user_msg=state["user_question"],
            tool_name=tool_name,
            tool_args=tool_args,
        )

    If allowed is False:
        - block the tool call
        - audit via guard_deny_and_raise(gate="PROMPT_INJECTION", reason=reason)
    """

    def __init__(self, policy_path: str | Path):
        path = Path(policy_path)
        if not path.exists():
            raise FileNotFoundError(f"injection policy not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self._policy = yaml.safe_load(f) or {}

        # phrases that imply jailbreak / override / policy evasion
        self.block_phrases: List[str] = [
            p.lower() for p in self._policy.get("block_phrases", [])
        ]

        # how many distinct targets are allowed in one call
        self.max_batch_targets: int = int(self._policy.get("max_batch_targets", 3))

        # which tools are considered "tracking control" / sensitive
        # (could also move to policy)
        self.tracking_tools = {
            "send_track",
            "send_cancel",
            "get_track_status",
        }

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def scan_single(
        self,
        *,
        user_msg: str,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Returns:
            (allowed: bool, reason: str)

        We run multiple sub-checks. First failure wins.
        """

        # 1. Jailbreak / override phrases check (user_msg + tool_args text)
        ok, reason = self._check_block_phrases(user_msg, tool_args)
        if not ok:
            return False, reason

        # 2. Broadcast / "everyone/all" language check
        ok, reason = self._check_mass_scope_language(user_msg, tool_args)
        if not ok:
            return False, reason

        # 3. Batch abuse check (too many IDs in one call)
        ok, reason = self._check_batch_targets(tool_name, tool_args)
        if not ok:
            return False, reason

        return True, "clean"

    # ---------------------------------------------------------
    # Internal checks
    # ---------------------------------------------------------

    def _check_block_phrases(
        self,
        user_msg: str,
        tool_args: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Look for phrases like:
        'ignore previous rules', 'override policy', 'bypass safety', etc.
        We check both the raw user_msg and any string values in tool_args,
        because LLMs may smuggle jailbreak text into the args.
        """
        blob_low = (user_msg or "").lower() + " " + self._args_blob(tool_args).lower()

        for phrase in self.block_phrases:
            if phrase in blob_low:
                return (
                    False,
                    f"Disallowed control phrase detected ('{phrase}'). "
                    "Possible jailbreak / policy override.",
                )

        return True, "ok"

    def _check_mass_scope_language(
        self,
        user_msg: str,
        tool_args: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Ban broadcast-scale instructions like:
        'track everyone', 'cancel tracking for all people', 'run for each person'.
        This matters because TRACKING is sensitive and should be per-ID,
        not bulk.
        """
        blob_low = (user_msg or "").lower() + " " + self._args_blob(tool_args).lower()

        mass_patterns = [
            r"\btrack (everyone|all|every person)\b",
            r"\bcancel tracking (for )?(everyone|all)\b",
            r"\bfor each (person|id)\b",
            r"\bloop through\b",
            r"\brun this for all\b",
            r"\bbulk\b",
        ]

        for pat in mass_patterns:
            if re.search(pat, blob_low):
                return (
                    False,
                    "Broadcast / mass-scope command detected. "
                    "Bulk control is not allowed.",
                )

        return True, "ok"

    def _check_batch_targets(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Enforce max_batch_targets for tracking-control tools.

        Two possible arg shapes we handle:
        - resolved_id: "X111"
        - resolved_ids: ["X111", "Y222", "Z333"]

        If caller tries to act on too many distinct IDs in a single tool call,
        we consider that a mass abuse pattern and block.
        """
        name_low = (tool_name or "").lower()
        if name_low not in {t.lower() for t in self.tracking_tools}:
            # Non-tracking tool -> skip batch abuse rule
            return True, "ok"

        ids: List[str] = []

        # Common single-target field
        rid = tool_args.get("resolved_id")
        if isinstance(rid, str) and rid.strip():
            ids.append(rid.strip())

        # Optional multi-target field if you allow batch ops
        rid_list = tool_args.get("resolved_ids")
        if isinstance(rid_list, list):
            for x in rid_list:
                if isinstance(x, str) and x.strip():
                    ids.append(x.strip())

        distinct_ids = set(ids)

        if len(distinct_ids) > self.max_batch_targets:
            return (
                False,
                f"Too many targets in one request "
                f"({len(distinct_ids)} > {self.max_batch_targets}). "
                "Bulk tracking is not allowed.",
            )

        return True, "ok"

    # ---------------------------------------------------------
    # Helper
    # ---------------------------------------------------------

    def _args_blob(self, tool_args: Dict[str, Any]) -> str:
        """
        Flatten tool_args to a scan-friendly text blob.
        We only stringify short scalars (to avoid dumping huge payloads).
        """
        parts: List[str] = []
        for k, v in (tool_args or {}).items():
            if isinstance(v, str):
                parts.append(v[:200])  # clip long LLM rambling
            elif isinstance(v, (int, float, bool)):
                parts.append(str(v))
        return " ".join(parts)
