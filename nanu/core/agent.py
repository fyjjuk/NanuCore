"""Clase base para agentes de NanuCore."""
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from nanu.core.interfaces import Tool, MemoryStore, VectorStore
from nanu.core.security.sandbox import WorkspaceSandbox
from nanu.core.providers import LLMRouter

class Agent:
    def __init__(self, config_path: str, llm_router: LLMRouter,
                 tools: List[Tool], memory: MemoryStore, vector_store: Optional[VectorStore] = None):
        self.config_path = Path(config_path)
        self._load_config()
        self.llm_router = llm_router
        self.tools = {tool.name: tool for tool in tools}
        self.memory = memory
        self.vector_store = vector_store
        self.workspace = WorkspaceSandbox(self.config.get('workspace', f"workspace/{self.id}"))
    
    def _load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.id = self.config['id']
        self.name = self.config['name']
        self.description = self.config.get('description', '')
        self.execution_mode = self.config.get('execution_mode', 'exclusive')
        self.short_term_memory_window = self.config.get('short_term_memory_window', 10)
        
        # Configuración de caché
        cache_cfg = self.config.get('cache', {})
        class CacheConf: pass
        self.cache_config = CacheConf()
        self.cache_config.enabled = cache_cfg.get('enabled', False)
        self.cache_config.ttl = cache_cfg.get('ttl', 3600)
    
    async def process(self, user_input: str, session_key: str) -> str:
        raise NotImplementedError("El pipeline se encarga del procesamiento")
    
    def get_route(self, route_id: str) -> Optional[Dict[str, Any]]:
        routes_dir = self.config_path.parent / "routes"
        if not routes_dir.exists():
            return None
        for yaml_file in routes_dir.glob("*.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                route = yaml.safe_load(f)
                if route.get('route_id') == route_id:
                    return route
        return None
