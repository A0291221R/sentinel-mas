# sentinel_mas/tools/loader.py
import importlib
import pkgutil
from typing import Dict

from langchain_core.tools import BaseTool as LCBaseTool


def load_langchain_decorated_tools() -> Dict[str, LCBaseTool]:
    import sentinel_mas.tools as tools_pkg

    reg: Dict[str, LCBaseTool] = {}
    for _, modname, _ in pkgutil.walk_packages(
        tools_pkg.__path__, tools_pkg.__name__ + "."
    ):
        module = importlib.import_module(modname)
        for attr in dir(module):
            val = getattr(module, attr)
            if isinstance(val, LCBaseTool):
                reg[val.name] = val

    return reg


def load_tools() -> Dict[str, LCBaseTool]:
    reg = load_langchain_decorated_tools()
    return reg
