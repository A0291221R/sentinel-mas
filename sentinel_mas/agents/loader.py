from __future__ import annotations

import glob
import os
from typing import Dict

import yaml

from sentinel_mas.tools import TOOL_REGISTRY

from .runtime import AgentRuntime


def load_agent_configs(config_dir: str) -> Dict[str, AgentRuntime]:
    agent_registry: Dict[str, AgentRuntime] = {}

    # for tool_name, tool in TOOL_REGISTRY.items():
    #     print(f"tool_name: {tool_name}")
    #     print(f"tool: {tool}")

    for path in glob.glob(os.path.join(config_dir, "*.yml")):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        name = raw["name"]
        llm_model = raw["llm"]["model"]
        llm_temp = float(raw["llm"].get("temperature", 0.0))
        llm_max_tokens = int(raw["llm"].get("max_tokens", 300))
        system_prompt = raw["system_prompt"]

        tool_names = raw.get("tools", [])
        tool_map = {}
        for tname in tool_names:
            if tname not in TOOL_REGISTRY:
                raise RuntimeError(f"[{name}] tool '{tname}' not found")
            tool_map[tname] = TOOL_REGISTRY[tname]

        runtime = AgentRuntime(
            name=name,
            system_prompt=system_prompt,
            llm_model=llm_model,
            llm_temperature=llm_temp,
            tools=tool_map,
            llm_max_tokens=llm_max_tokens,
        )
        agent_registry[name] = runtime
    return agent_registry
