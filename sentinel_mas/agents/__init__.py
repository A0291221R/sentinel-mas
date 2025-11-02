from pathlib import Path

from sentinel_mas.agents.loader import load_agent_configs

_MODULE_DIR = Path(__file__).parent.resolve()
_CONFIG_DIR = _MODULE_DIR / "agent_configs"

AGENT_REGISTRY = load_agent_configs(str(_CONFIG_DIR))
