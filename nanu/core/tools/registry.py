from typing import Dict, Optional, List
from nanu.core.interfaces import Tool

class ToolRegistry:
    _instance = None
    _tools: Dict[str, Tool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            # No lanzar error, solo advertir (para evitar duplicados)
            print(f"⚠️ Herramienta '{tool.name}' ya registrada, ignorando.")
            return
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)
    
    def list(self) -> List[str]:
        return list(self._tools.keys())
    
    def unregister(self, name: str) -> None:
        if name in self._tools:
            del self._tools[name]
    
    def register_builtin(self) -> None:
        from nanu.core.tools.builtin.filesystem import FilesystemTool
        from nanu.core.tools.builtin.shell import ShellTool
        self.register(FilesystemTool())
        self.register(ShellTool())
        print(f"[ToolRegistry] Builtin tools registradas: {self.list()}")
