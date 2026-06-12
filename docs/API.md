# API de NanuCore 3.0

## Core Modules

### Agent

```python
class Agent:
    def __init__(self, config_path: str, llm_clients: Dict[str, LLMClient],
                 tools: List[Tool], memory: MemoryStore, vector_store: Optional[VectorStore] = None)

    # Atributos
    id: str
    name: str
    config: Dict
    tools: Dict[str, Tool]
    workspace: WorkspaceSandbox
    memory: MemoryStore
    cache_config: CacheConf

    # Métodos
    def get_route(self, route_id: str) -> Optional[Dict]
```

### Pipeline

```python
class Pipeline:
    async def run(self, agent: Agent, user_input: str, session_key: str) -> Tuple[str, Dict]
    def get_hook_manager(self) -> HookManager
```

### HookManager

```python
class HookManager:
    def add_pre_hook(self, hook: Callable[[str, Dict], Awaitable[str]])
    def add_post_hook(self, hook: Callable[[str, Dict], Awaitable[str]])
    def add_error_hook(self, hook: Callable[[Exception, str, Dict], Awaitable[None]])
```

### Tool

```python
class Tool(ABC):
    name: str
    description: str
    enabled: bool = True

    @abstractmethod
    async def execute(self, args: Dict[str, Any], workspace: Optional[WorkspaceSandbox] = None) -> str
```

### MemoryStore

```python
class MemoryStore(Protocol):
    async def add(self, session_key: str, turn: Dict[str, Any]) -> None
    async def get_history(self, session_key: str, limit: int = 10) -> List[Dict[str, Any]]
    async def clear(self, session_key: str) -> None
```

### VectorStore

```python
class VectorStore(Protocol):
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]
    async def index(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None
    async def delete_namespace(self, namespace: str) -> None
```

### EventBus

```python
class EventBus:
    def subscribe(self, event: str, handler: Callable[[Any], Awaitable[None]])
    async def publish(self, event: str, data: Any) -> None
```

---

## Security

### WorkspaceSandbox

```python
class WorkspaceSandbox:
    def resolve_path(self, user_path: str) -> Path
    def safe_open(self, path: str, mode: str = 'r')
    def safe_listdir(self, path: str = ".") -> List[str]
    def safe_exists(self, path: str) -> bool
    def safe_mkdir(self, path: str, exist_ok: bool = True)
    def safe_rm(self, path: str, recursive: bool = False)
    def safe_write_text(self, path: str, content: str)
    def safe_read_text(self, path: str) -> str
```

### CredentialManager

```python
class CredentialManager:
    def encrypt(self, plaintext: str) -> str
    def decrypt(self, encrypted: str) -> str
    @classmethod
    def from_env(cls, env_var: str = "NANU_CREDENTIAL_PASSPHRASE") -> Optional['CredentialManager']
```

### Gatekeeper

```python
class Gatekeeper:
    async def verify(self, route_id: str, route_config: Dict, request_id: str, session_id: str = None) -> bool
```

---

## Memory

### JSONLMemory

```python
class JSONLMemory:
    async def add(self, session_key: str, turn: Dict[str, Any]) -> None
    async def get_history(self, session_key: str, limit: int = 10) -> List[Dict[str, Any]]
    async def clear(self, session_key: str) -> None
```

### SQLiteVectorStore

```python
class SQLiteVectorStore:
    async def index(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None
    async def search(self, query: str, top_k: int = 5, namespace: Optional[str] = None) -> List[Dict[str, Any]]
    async def delete_namespace(self, namespace: str) -> None
```

---

## Channels

### CLIChannel

```python
class CLIChannel:
    async def run(self) -> None
```

### WebSocketChannel

```python
class WebSocketChannel:
    async def start(self) -> None
    async def stop(self) -> None
```

---

## Tools

### ToolRegistry

```python
class ToolRegistry:
    def register(self, tool: Tool) -> None
    def get(self, name: str) -> Optional[Tool]
    def list(self) -> List[str]
    def register_builtin(self) -> None
```

### Builtin Tools

**FilesystemTool**

- `read(path)` - Leer archivo
- `write(path, content)` - Escribir archivo
- `list(path)` - Listar directorio
- `mkdir(path)` - Crear directorio
- `rm(path, recursive=False)` - Eliminar
- `exists(path)` - Verificar existencia

**ShellTool** (deshabilitada por defecto)

- `shell(command)` - Ejecutar comando (solo allowlist: ls, cat, head, etc.)

---

## Cache

### DiskCache

```python
class DiskCache:
    def get(self, agent_id: str, route_id: str, prompt: str, system_prompt: str = "") -> Optional[str]
    def set(self, agent_id: str, route_id: str, prompt: str, response: str, system_prompt: str = "", ttl: int = 3600)
    def invalidate(self, agent_id: Optional[str] = None, route_id: Optional[str] = None)
```
