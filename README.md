# 🚀 NanuCore 3.0

**Framework multi-agente para asistentes de IA con arquitectura modular, canales concurrentes y seguridad integrada.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![WebSocket](https://img.shields.io/badge/WebSocket-Enabled-green.svg)]()

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [Canales de Comunicación](#-canales-de-comunicación)
- [Sistema de Hooks](#-sistema-de-hooks)
- [Seguridad](#-seguridad)
- [Skills y Herramientas](#-skills-y-herramientas)
- [API de Agentes](#-api-de-agentes)
- [Ejemplos](#-ejemplos)
- [Roadmap](#-roadmap)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## ✨ Características

- **Multi-agente**: Soporta múltiples agentes especializados (Spotify, D&D, Dev Assistant)
- **Canales concurrentes**: CLI interactivo + WebSocket nativo (más canales en desarrollo)
- **Arquitectura modular**: Fácil extensión con skills y herramientas
- **Seguridad multicapa**: Workspace sandbox, Gatekeeper humano, Ingress/Egress filters
- **Memoria persistente**: JSONL append-only + búsqueda semántica con SQLite FTS5
- **Caché inteligente**: Respuestas cacheadas con TTL configurable
- **Sistema de hooks**: Pre/Post procesamiento, manejo de errores
- **LLM asíncrono**: Soporte para Ollama (Gemini, Groq en progreso)

---

## 🏗️ Arquitectura

```
NanuCore 3.0
├── nanu/core/              # Núcleo del sistema
│   ├── agent.py            # Clase base Agent
│   ├── orchestrator.py     # Gestor de agentes
│   ├── pipeline.py         # Pipeline principal con hooks
│   ├── events/             # EventBus y Hooks
│   ├── memory/             # JSONLMemory, SQLiteVectorStore
│   ├── security/           # Sandbox, Credential, Gatekeeper
│   ├── routing/            # IntentRouter, ModelRouter
│   ├── providers/          # LLM clients (Ollama)
│   ├── tools/              # ToolRegistry, builtin tools
│   ├── skills/             # SkillLoader
│   └── channels/           # CLIChannel, WebSocketChannel
├── agents/                 # Agentes definidos por el usuario
├── nanu/data/              # Datos persistentes (memoria, caché)
└── main.py                 # Punto de entrada con canales concurrentes
```

### Flujo del Pipeline

```
Input → Pre-hooks → Sanitize → Ingress → Pre-route → IntentRouter → Post-route
→ Gatekeeper → ModelRouter → Execute (Cognitive/Script) → Post-hooks → Egress → Output
```

---

## 📦 Instalación

### Requisitos previos

- Python 3.11 o superior
- Ollama (para LLM local) o API keys para otros proveedores
- (Opcional) playerctl para control Spotify

### Pasos

```bash
# Clonar repositorio
git clone https://github.com/fyjjuk/nanu-core.git
cd nanu-core

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# Ejecutar
python main.py
```

---

## 🚀 Uso Rápido

### CLI Interactivo

```bash
python main.py
```

Comandos disponibles:

- `/help` - Muestra ayuda
- `/exit`, `/quit`, `/salir` - Salir
- `/agent list` - Listar agentes disponibles
- `/agent switch <id>` - Cambiar de agente
- `/clear` - Limpiar pantalla

### WebSocket

```python
import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as ws:
        # Listar agentes
        await ws.send(json.dumps({"type": "list_agents"}))
        response = await ws.recv()
        print(f"Agentes: {response}")

        # Seleccionar agente
        await ws.send(json.dumps({"type": "select_agent", "agent_id": "spotify_player"}))
        response = await ws.recv()
        print(f"Selección: {response}")

        # Enviar mensaje
        await ws.send(json.dumps({"type": "message", "text": "estado"}))
        response = await ws.recv()
        print(f"Respuesta: {response}")

asyncio.run(test())
```

---

## 🔌 Canales de Comunicación

### CLIChannel

Canal interactivo por consola con autocompletado, historial y comandos slash.

```python
from nanu.core.channels.cli import CLIChannel
channel = CLIChannel(orchestrator)
await channel.run()
```

### WebSocketChannel

Servidor WebSocket concurrente para integración con apps web.

```python
from nanu.core.channels.websocket import WebSocketChannel
channel = WebSocketChannel(orchestrator, host="localhost", port=8765)
await channel.start()  # Corre en segundo plano
```

### Crear un canal personalizado

```python
from nanu.core.channels.base import Channel

class MyChannel(Channel):
    async def run(self):
        # Implementar lógica del canal
        pass
```

---

## 🪝 Sistema de Hooks

Los hooks permiten extender el pipeline sin modificar su código.

### Tipos de hooks

| Hook | Momento | Parámetros |
|---|---|---|
| `pre_process` | Antes de sanitizar | `(input, context)` |
| `pre_route` | Después de sanitizar, antes de enrutar | `(input, context)` |
| `post_route` | Después de enrutar | `(route_id, input, context)` |
| `post_process` | Después de generar respuesta | `(response, context)` |
| `on_error` | Cuando ocurre una excepción | `(error, input, context)` |

### Ejemplo

```python
async def log_hook(user_input: str, context: dict) -> str:
    print(f"Procesando: {user_input}")
    return user_input

pipeline = Pipeline()
pipeline.get_hook_manager().add_pre_hook(log_hook)
```

---

## 🔒 Seguridad

### Workspace Sandbox

Aísla las operaciones de archivo a un directorio específico.

```python
from nanu.core.security.sandbox import WorkspaceSandbox
sandbox = WorkspaceSandbox("workspace/agent")
sandbox.safe_write_text("file.txt", "content")  # Solo dentro del workspace
```

### Gatekeeper

Aprobación humana para operaciones sensibles.

```yaml
# En route.yaml
gatekeeper_required: true
gatekeeper_timeout: 30  # segundos
```

### Credential Manager

Cifrado de credenciales con AES-256-GCM.

```python
from nanu.core.security.credential import CredentialManager
manager = CredentialManager.from_env()
encrypted = manager.encrypt("api_key_123")
decrypted = manager.decrypt(encrypted)
```

---

## 🛠️ Skills y Herramientas

### Crear una Skill

```yaml
# nanu/skills/mi_skill/skill.yaml
name: "Mi Skill"
description: "Habilidades personalizadas"
version: "1.0.0"
tools:
  - name: "mi_herramienta"
    class: "MiHerramienta"
```

```python
# nanu/skills/mi_skill/tools/mi_herramienta.py
from nanu.core.interfaces import Tool

class MiHerramienta(Tool):
    name = "mi_herramienta"
    description = "Ejecuta una acción personalizada"
    enabled = True

    async def execute(self, args: dict, workspace=None) -> str:
        # Implementación
        return "Resultado"
```

### Herramientas Builtin

- `filesystem`: Operaciones de archivo con sandbox
- `shell`: Comandos shell restringidos (deshabilitada por defecto)

---

## 📚 API de Agentes

### Configuración de agente (`config.yaml`)

```yaml
id: "mi_agente"
name: "Mi Agente"
description: "Descripción"
workspace: "workspace/mi_agente"
short_term_memory_window: 10
execution_mode: "parallel"  # exclusive | parallel
llm_provider:
  name: "ollama"
  model: "llama3.2:3b"
  light_model: "phi3:mini"
  heavy_model: "llama3.2:3b"
  temperature: 0.7
  max_tokens: 4096
tools:
  native:
    - name: "filesystem"
      enabled: true
cache:
  enabled: true
  ttl: 3600
router_config:
  mode: "keyword"
  threshold: 0.2
```

### Definir rutas (`routes/*.yaml`)

```yaml
route_id: "mi_ruta"
type: "script"  # o "cognitive"
description: "palabra clave1, palabra clave2"
script_path: "tools/mi_script.py"
script_args:
  action: "ejecutar"
gatekeeper_required: false
```

---

## 💡 Ejemplos

### Agente Spotify (funcional)

```bash
python main.py
# Seleccionar Spotify Controller
> play           # Reproducir
> pause          # Pausar
> next           # Siguiente
> previous       # Anterior
> status         # Estado
> busca canción  # Buscar
```

### Agente D&D (en migración)

```bash
> crea un personaje llamado Gandalf clase Mago raza Elfo
> muestra la ficha de Gandalf
> añade poción al inventario de Gandalf
> muestra el inventario de Gandalf
```

---

## 🗺️ Roadmap

### Completado ✅

- Núcleo modular (interfaces, seguridad, memoria)
- Agente y Orquestador
- Routing inteligente (keyword + model router)
- Herramientas builtin (filesystem, shell)
- Sistema de Skills
- Canales CLI y WebSocket
- Caché en disco
- Gatekeeper mejorado
- EventBus y Hooks

### En progreso 🚧

- Pruebas unitarias
- Migración completa de agentes (D&D, Dev Assistant)
- Documentación Sphinx

### Futuro 🔮

- Canal Telegram
- Canal Discord
- MCP nativo
- Dashboard web con WebSockets

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request

### Estilo de código

- Type hints obligatorios
- Docstrings en formato Google
- Tests con pytest-asyncio

---

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)

## 🙏 Agradecimientos

Inspirado en PicoClaw y su arquitectura modular.  
Desarrollado con ❤️ por Fernando (ferdoNAN)
