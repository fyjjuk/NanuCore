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
- [Configuración Avanzada](#-configuración-avanzada)
- [Ejemplos](#-ejemplos)
- [Roadmap](#-roadmap)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## ✨ Características

- **Multi-agente**: Agentes especializados (Spotify, D&D, Dev Assistant) con configuración YAML
- **Canales concurrentes**: CLI interactivo + WebSocket nativo + Voz (Linux)
- **Arquitectura modular**: Fácil extensión con skills, herramientas y hooks
- **Seguridad multicapa**: Workspace sandbox, Gatekeeper humano, Credential Manager (AES-256-GCM)
- **Memoria persistente**: JSONL append-only + búsqueda semántica con SQLite FTS5
- **Caché inteligente**: Respuestas cacheadas con TTL configurable e invalidación selectiva por agente/ruta
- **Sistema de hooks**: Pre/Post procesamiento, manejo de errores, filtros de entrada/salida
- **LLM multi-proveedor**: Ollama (principal), Gemini, Groq, OpenRouter, Cerebras, Mistral con fallback y rotación
- **Rate limiting inteligente**: Token bucket por proveedor LLM para evitar saturación de APIs
- **STT bilingüe**: Faster-Whisper (inglés/español) + fallback a Vosk (solo español)
- **Rotación automática de API keys**: Gemini soporta múltiples claves con cooldown por fallos/rate limit
- **Auditoría persistente**: Gatekeeper con logs JSONL y caché de aprobación por sesión
- **RAG ligero**: Búsqueda semántica con SQLite FTS5 (sin dependencias externas)

---

## 🏗️ Arquitectura

NanuCore 3.0
├── nanu/core/              # Núcleo del sistema
│   ├── agent.py            # Clase base Agent
│   ├── orchestrator.py     # Gestor de agentes
│   ├── pipeline.py         # Pipeline principal con hooks
│   ├── events/             # EventBus y Hooks
│   ├── memory/             # JSONLMemory, SQLiteVectorStore
│   ├── security/           # Sandbox, Credential, Gatekeeper
│   ├── routing/            # IntentRouter, ModelRouter
│   ├── providers/          # LLM clients (Ollama, Gemini, Groq, ...)
│   ├── tools/              # ToolRegistry, builtin tools
│   ├── skills/             # SkillLoader
│   └── channels/           # CLIChannel, WebSocketChannel, VoiceChannel
├── agents/                 # Agentes definidos por el usuario
├── nanu/data/              # Datos persistentes (memoria, caché, vectores, auditoría)
└── main.py                 # Punto de entrada con canales concurrentes

### Flujo del Pipeline

Input → Pre-hooks → Corrección fonética → Sanitize → Ingress → Pre-route → IntentRouter → Post-route → Gatekeeper → ModelRouter → Execute (Cognitive/Script) → Post-hooks → Egress → Output

---

## 📦 Instalación

### Requisitos previos

- Python 3.11 o superior
- Ollama (para LLM local) o API keys para Gemini/Groq/OpenRouter/Cerebras/Mistral
- (Opcional) playerctl para control Spotify (Linux)
- (Opcional) mpg123, arecord y edge-tts para asistente de voz (Linux)

### Pasos

git clone https://github.com/fyjjuk/NanuCore.git
cd NanuCore

python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

pip install -r requirements-extra.txt

pip install faster-whisper

cp .env.example .env

python main.py

### Dependencias del sistema (Linux)

sudo pacman -S alsa-utils mpg123 playerctl  # Arch Linux

---

## 🚀 Uso Rápido

### CLI Interactivo

python main.py

Comandos disponibles:

/help - Muestra ayuda
/exit, /quit, /salir - Salir
/agent list - Listar agentes disponibles
/agent switch <id> - Cambiar de agente
/agent info - Mostrar detalles del agente (LLM, proveedores)
/routes - Mostrar rutas del agente activo
/learn "original" "corregido" - Añadir corrección fonética
/list-corrections, /lc - Listar correcciones guardadas
/export-corrections, /ec - Exportar correcciones a archivo JSON
/clear - Limpiar pantalla

### WebSocket

import asyncio
import websockets
import json

async def test():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"type": "list_agents"}))
        response = await ws.recv()
        print(f"Agentes: {response}")

        await ws.send(json.dumps({"type": "select_agent", "agent_id": "spotify_spicetify"}))
        response = await ws.recv()
        print(f"Selección: {response}")

        await ws.send(json.dumps({"type": "message", "text": "estado"}))
        response = await ws.recv()
        print(f"Respuesta: {response}")

asyncio.run(test())

---

## 🔌 Canales de Comunicación

### CLIChannel

Canal interactivo por consola con autocompletado y comandos slash.

from nanu.core.channels.cli import CLIChannel
channel = CLIChannel(orchestrator)
await channel.run()

### WebSocketChannel

Servidor WebSocket concurrente para integración con apps web.

from nanu.core.channels.websocket import WebSocketChannel
channel = WebSocketChannel(orchestrator, host="localhost", port=8765)
await channel.start()

### VoiceChannel (Linux)

Canal de voz con hotkey Copilot (F23) y TTS con edge-tts.

from nanu.core.channels.voice import VoiceChannel
voice = VoiceChannel(agent)
await voice.run()

### Crear un canal personalizado

from nanu.core.channels.base import Channel

class MyChannel(Channel):
    async def run(self):
        pass

---

## 🪝 Sistema de Hooks

Los hooks permiten extender el pipeline sin modificar su código.

Tipos de hooks:

| Hook | Momento | Parámetros |
|---|---|---|
| pre_process | Antes de sanitizar | (input, context) |
| pre_route | Después de sanitizar, antes de enrutar | (input, context) |
| post_route | Después de enrutar | (route_id, input, context) |
| post_process | Después de generar respuesta | (response, context) |
| on_error | Cuando ocurre una excepción | (error, input, context) |

### Ejemplo

async def log_hook(user_input: str, context: dict) -> str:
    print(f"Procesando: {user_input}")
    return user_input

pipeline = Pipeline()
pipeline.get_hook_manager().add_pre_hook(log_hook)

---

## 🔒 Seguridad

### Workspace Sandbox

from nanu.core.security.sandbox import WorkspaceSandbox
sandbox = WorkspaceSandbox("workspace/agent")
sandbox.safe_write_text("file.txt", "content")

### Gatekeeper

gatekeeper_required: true
gatekeeper_timeout: 30

### Credential Manager

from nanu.core.security.credential import CredentialManager
manager = CredentialManager.from_env()
encrypted = manager.encrypt("api_key_123")
decrypted = manager.decrypt(encrypted)

---

## 🛠️ Skills y Herramientas

### Crear una Skill

name: "Mi Skill"
description: "Habilidades personalizadas"
version: "1.0.0"
tools:
  - name: "mi_herramienta"
    class: "MiHerramienta"

from nanu.core.interfaces import Tool

class MiHerramienta(Tool):
    name = "mi_herramienta"
    description = "Ejecuta una acción personalizada"
    enabled = True

    async def execute(self, args: dict, workspace=None) -> str:
        return "Resultado"

### Herramientas Builtin

- filesystem: Operaciones de archivo con sandbox
- shell: Comandos shell restringidos (deshabilitada por defecto)

---

## 📚 API de Agentes

### Configuración de agente (config.yaml)

id: "mi_agente"
name: "Mi Agente"
description: "Descripción"
workspace: "workspace/mi_agente"
short_term_memory_window: 10
execution_mode: "exclusive"

llm:
  providers:
    - type: "ollama"
      name: "ollama"
      model: "phi3:mini"
      host: "http://localhost:11434"
      temperature: 0.7
      max_tokens: 4096
      rate_limit_max_requests: 5
      rate_limit_per_seconds: 10
    - type: "gemini"
      name: "gemini"
      priority: 1
      model: "gemini-2.0-flash-exp"
      temperature: 0.7
      max_tokens: 4096
    - type: "groq"
      name: "groq"
      priority: 2
      model: "llama-3.3-70b-versatile"
      temperature: 0.7
      max_tokens: 4096

tools:
  native:
    - name: "filesystem"
      enabled: true
    - name: "mi_herramienta"
      script: "tools/mi_herramienta.py"
      enabled: true

cache:
  enabled: true
  ttl: 3600

router_config:
  mode: "keyword"
  threshold: 0.2

voice:
  enabled: true
  provider: edge
  voice_id: "es-ES-ElviraNeural"

### Definir rutas (routes/*.yaml)

route_id: "mi_ruta"
type: "script"
description: "palabra clave1, palabra clave2"
script_path: "tools/mi_script.py"
script_args:
  action: "ejecutar"
  param: "{user_input}"
gatekeeper_required: false

---

## ⚙️ Configuración Avanzada

### Múltiples API keys de Gemini

GOOGLE_API_KEY_1=tu_primera_key
GOOGLE_API_KEY_2=tu_segunda_key
GOOGLE_API_KEY_3=tu_tercera_key

Cooldown por defecto:
- 429 (Rate limit): 60 segundos
- 403 (Key inválida): 300 segundos
- Timeout/Error de conexión: 30 segundos

### STT con Faster-Whisper (bilingüe)

pip install faster-whisper

python -c "from faster_whisper import WhisperModel; print('OK')"

### Rate limiting por proveedor LLM

llm:
  providers:
    - type: "gemini"
      rate_limit_max_requests: 5
      rate_limit_per_seconds: 10

### Invalidación selectiva de caché

from nanu.core.cache import DiskCache
cache = DiskCache()

cache.invalidate()
cache.invalidate(agent_id="spotify_spicetify")
cache.invalidate(agent_id="spotify_spicetify", route_id="search")
cache.invalidate(pattern="spotify_*")

---

## 💡 Ejemplos

### Agente Spotify (funcional)

python main.py
> play
> pause
> next
> previous
> status
> volumen 50
> volumen 100
> sube el volumen
> busca canción

### Agente D&D (ejemplo)

> crea un personaje llamado Gandalf clase Mago raza Elfo
> muestra la ficha de Gandalf
> añade poción al inventario de Gandalf
> muestra el inventario de Gandalf

---

## 🗺️ Roadmap

### Completado ✅

- Núcleo modular (interfaces, seguridad, memoria)
- Agente y Orquestador
- Routing inteligente (keyword + model router con coincidencia difusa)
- Herramientas builtin (filesystem, shell)
- Sistema de Skills
- Canales CLI, WebSocket y Voz
- Caché en disco con invalidación selectiva
- Gatekeeper mejorado con caché por sesión y auditoría persistente
- EventBus y Hooks
- Soporte multi-LLM (Ollama, Gemini, Groq, OpenRouter, Cerebras, Mistral)
- Rate limiting por proveedor (token bucket)
- Rotación automática de API keys con cooldown
- Sistema de correcciones fonéticas
- STT con Faster-Whisper (bilingüe) + fallback Vosk
- Workspace sandbox con protección contra symlink attacks
- Sanitización y filtrado de entrada/salida

### En progreso 🚧

- Pruebas unitarias completas
- Documentación Sphinx
- Integración MCP (Model Context Protocol)

### Futuro 🔮

- Canal Telegram
- Canal Discord
- Dashboard web con WebSockets
- Routing semántico con embeddings
- Soporte multiplataforma para voz (Windows/macOS)

---

## 🤝 Contribuir

1. Fork el repositorio
2. Crear rama de feature (git checkout -b feature/nueva-funcionalidad)
3. Commit cambios (git commit -m "Añadir nueva funcionalidad")
4. Push (git push origin feature/nueva-funcionalidad)
5. Abrir Pull Request

### Estilo de código

- Type hints obligatorios
- Docstrings en formato Google
- Tests con pytest-asyncio

---

## 📄 Licencia

MIT License - ver LICENSE

## 🙏 Agradecimientos

Inspirado en PicoClaw y su arquitectura modular.
Desarrollado con ❤️ por Fernando (ferdoNAN)
