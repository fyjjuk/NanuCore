from typing import Optional, Dict
from pydantic import BaseModel, Field
from typing import Optional, Any, List, Literal, Dict

class RAGConfig(BaseModel):
    enabled: bool = False
    namespace: Optional[str] = None
    top_k: int = 5
    similarity_threshold: float = 0.75

class RouterConfig(BaseModel):
    mode: Literal["keyword", "ollama", "embedding", "hybrid"] = "keyword"
    model: Optional[str] = None
    threshold: float = 0.3

class SanitizerConfig(BaseModel):
    enabled: bool = True
    use_llm: bool = False
    model: Optional[str] = None

class CacheConfig(BaseModel):
    enabled: bool = False
    ttl: int = 3600

class AgentManifest(BaseModel):
    id: str
    name: str
    description: str = ""
    short_term_memory_window: int = 5
    execution_mode: Literal["exclusive", "parallel"] = "exclusive"
    execution_timeout: int = 30
    rag_config: RAGConfig = Field(default_factory=RAGConfig)
    router_config: RouterConfig = Field(default_factory=RouterConfig)
    sanitizer_config: SanitizerConfig = Field(default_factory=SanitizerConfig)
    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    llm_provider: dict = Field(default_factory=dict)
    llm_client: Optional[Any] = None
    memory: Optional[Any] = None
    long_term_memory: Optional[Any] = None
    firewall_override: dict = Field(default_factory=dict)
    routes_available: List[dict] = Field(default_factory=list)
    tools: dict = Field(default_factory=dict)
    voice_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

# Añadir al final de las importaciones, o modificar la clase AgentManifest
# Buscamos la clase AgentManifest y añadimos un nuevo campo
