# sentinel_mas/tools/mcp_loader.py
from __future__ import annotations
import os
from typing import Dict, Any, List
from langchain_core.tools import BaseTool, Tool

# Pseudocode: replace with the actual MCP client you use
class MCPClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 20.0):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
    def list_tools(self) -> List[Dict[str, Any]]:
        # return [{"name":"detect_objects","description":"...","schema":{...}}, ...]
        ...
    def invoke(self, tool_name: str, args: Dict[str, Any]) -> Any:
        # POST {base_url}/tools/{tool_name} with args; return JSON
        ...

def make_langchain_tool(server_name: str, client: MCPClient, spec: Dict[str, Any]) -> BaseTool:
    # Namespaced tool name
    tname = f"mcp:{server_name}:{spec['name']}"
    desc  = f"[MCP:{server_name}] {spec.get('description','')}".strip()

    # If you have JSON schema, you can build a StructuredTool; for brevity we use generic Tool
    def _run(**kwargs):
        return client.invoke(spec["name"], kwargs)

    return Tool(name=tname, description=desc, func=_run)

def load_mcp_tools_from_env() -> Dict[str, BaseTool]:
    """
    Discover MCP servers from env like:
      MCP_SERVERS=vision-mcp,files-mcp
      MCP_vision-mcp_URL=http://vision:7000
      MCP_vision-mcp_TOKEN=...
      MCP_files-mcp_URL=http://files:7100
    """
    registry: Dict[str, BaseTool] = {}
    servers = [s.strip() for s in os.getenv("MCP_SERVERS","").split(",") if s.strip()]
    for server in servers:
        base_url = os.getenv(f"MCP_{server}_URL")
        token    = os.getenv(f"MCP_{server}_TOKEN")
        if not base_url:
            continue
        client = MCPClient(base_url, token=token)
        for spec in client.list_tools():
            tool = make_langchain_tool(server, client, spec)
            registry[tool.name] = tool
    return registry
