from .loader import load_tools

# Load all tools immediately
TOOL_REGISTRY = load_tools()

# from .tracking_tools import TOOLS as TRACKING_TOOLS
# TOOL_REGISTRY.update(TRACKING_TOOLS)
