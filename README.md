# 🚀 NanuCore

**Framework multi-agente para asistentes de voz y automatización local**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📖 ¿Qué es NanuCore?

NanuCore es un framework ligero y modular para construir asistentes de IA locales que entienden comandos de voz y ejecutan acciones en tu sistema. Fue creado como alternativa a herramientas como Hermes o PicoClaw, priorizando:

- Velocidad y bajo consumo de recursos.
- Control total sobre el código y la privacidad de los datos.
- Extensibilidad sin depender de servicios en la nube.

Su principal caso de uso es el control por voz de aplicaciones locales (Spotify, luces, etc.) y la automatización de tareas personales.

---

## ✨ Características

| Área | Funcionalidad |
|------|---------------|
| Voz | STT con Faster-Whisper (bilingüe) y TTS con edge-tts. |
| Multi-agente | Varios agentes especializados (Spotify, D&D, Dev Assistant) con configuración YAML. |
| Canales | CLI interactivo, WebSocket y voz (Linux). |
| Seguridad | Sandbox de archivos, Gatekeeper humano, cifrado de credenciales y auditoría. |
| Memoria | Historial persistente en JSONL y búsqueda semántica con SQLite FTS5. |
| Caché | Respuestas cacheadas con invalidación selectiva. |
| LLM | Soporte para múltiples proveedores (Ollama, Gemini, Groq, etc.) con rotación de API keys. |
| Extensible | Hooks, habilidades (skills), herramientas nativas y canales personalizados. |

---

## 🔧 Instalación

### Requisitos

- Python 3.11 o superior.
- Ollama (para LLM local) o API keys de Gemini/Groq.
- (Opcional) playerctl para controlar Spotify.
- (Opcional) alsa-utils, mpg123 y edge-tts para voz.

### Pasos

git clone https://github.com/fyjjuk/NanuCore.git
cd NanuCore

python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

pip install -r requirements-extra.txt

cp .env.example .env

python main.py

---

## 🎮 Uso rápido: Control por voz de Spotify

Asegúrate de que Spotify esté abierto y reproduciendo.

Ejecuta python main.py y selecciona el agente spotify_spicetify.

Si el agente tiene voice.enabled: true, presiona la tecla Copilot (F23) para hablar.

Comandos de voz soportados:

"play"          Reproducir
"pause"         Pausar
"next"          Siguiente canción
"previous"      Canción anterior
"status"        Mostrar canción actual
"busca [nombre]"Buscar y reproducir
"volumen 50"    Cambiar volumen

---

## 🏗️ Estructura del proyecto

NanuCore/
├── agents/                  # Agentes (cada uno con su config.yaml y rutas)
│   ├── spotify_spicetify/   # Control de Spotify (funcional)
│   ├── test_agent/          # Agente de pruebas
│   └── ...
├── config/                  # Catálogos de modelos (models.yaml)
├── data/                    # Datos persistentes
├── docs/                    # Documentación
├── examples/                # Agentes de ejemplo
├── nanu/                    # Núcleo del framework
│   ├── core/                # Módulos fundamentales
│   │   ├── audio/           # STT, TTS, sanitización
│   │   ├── channels/        # CLI, WebSocket, Voz
│   │   ├── events/          # EventBus y hooks
│   │   ├── memory/          # JSONLMemory, SQLiteVectorStore
│   │   ├── providers/       # Clientes LLM
│   │   ├── routing/         # IntentRouter, ModelRouter
│   │   ├── security/        # Sandbox, CredentialManager, Gatekeeper
│   │   ├── skills/          # SkillLoader
│   │   ├── tools/           # ToolRegistry, herramientas builtin
│   │   ├── utils/           # Utilidades (sanitización)
│   │   ├── agent.py         # Clase base Agent
│   │   ├── cache.py         # Caché con invalidación selectiva
│   │   ├── interfaces.py    # Interfaces para extensibilidad
│   │   ├── logging.py       # Logging estructurado
│   │   ├── orchestrator.py  # Gestor de agentes
│   │   └── pipeline.py      # Pipeline principal
│   └── data/                # Archivos de datos
├── .env.example             # Variables de entorno
├── main.py                  # Punto de entrada
├── requirements.txt         # Dependencias core
├── requirements-extra.txt   # Dependencias opcionales
└── README.md                # Este archivo

---

## 🛠️ Personalización y extensión

### Crear un nuevo agente

mkdir -p agents/mi_agente/{routes,tools}

### agents/mi_agente/config.yaml

id: "mi_agente"
name: "Mi Agente"
description: "Descripción"
workspace: "workspace/mi_agente"
llm:
  providers:
    - type: "ollama"
      model: "phi3:mini"
tools:
  native:
    - name: "mi_herramienta"
      script: "tools/mi_herramienta.py"
      enabled: true
router_config:
  mode: "keyword"
  threshold: 0.2
voice:
  enabled: true

### agents/mi_agente/routes/accion.yaml

route_id: "accion"
type: "script"
description: "palabra clave1, palabra clave2"
script_path: "tools/mi_herramienta.py"
script_args:
  action: "ejecutar"

### agents/mi_agente/tools/mi_herramienta.py

import json
import sys

def run(args):
    return {"result": "Hecho"}

if __name__ == "__main__":
    print(json.dumps(run(json.loads(sys.argv[1]))))

### Añadir un hook personalizado

from nanu.core.events.hooks import HookManager

async def mi_hook(user_input: str, context: dict) -> str:
    print(f"Procesando: {user_input}")
    return user_input

pipeline = Pipeline()
pipeline.get_hook_manager().add_pre_hook(mi_hook)

---

## ⚠️ Limitaciones conocidas

- STT: Faster-Whisper con modelo base en CPU puede tener precisión limitada con nombres propios.
- Voz: Solo funciona en Linux (por dependencias arecord, evdev y mpg123).
- Rendimiento: Modelos locales en CPU tienen latencia; se recomienda GPU.
- Compatibilidad: El control de Spotify requiere la aplicación de escritorio abierta.

---

## 📄 Licencia

MIT License - ver LICENSE

---

## 🙏 Agradecimientos

Inspirado en la necesidad de un asistente local rápido y controlable. Desarrollado con ❤️ por Fernando (ferdoNAN).

---

## 🗺️ Hoja de ruta

| Estado | Funcionalidad |
|--------|---------------|
| ✅ | Núcleo modular (seguridad, memoria, routing) |
| ✅ | Agentes con configuración YAML y herramientas |
| ✅ | Canales CLI, WebSocket y Voz (Linux) |
| ✅ | Soporte multi-LLM (Ollama, Gemini, Groq) |
| ✅ | Caché e invalidación selectiva |
| ✅ | Gatekeeper humano y auditoría |
| ⚠️ | Pruebas unitarias (en progreso) |
| 🔜 | Integración MCP |
| 🔜 | Canal Telegram |
| 🔜 | Dashboard web |

---

## 💬 Preguntas frecuentes

### ¿Puedo usar NanuCore sin micrófono?

Sí, funciona perfectamente desde la CLI con entrada de texto.

### ¿Necesito conexión a Internet?

No, excepto para servicios externos (Gemini, Groq) si se configuran. El core funciona completamente offline.

### ¿Puedo usar otros LLM como GPT o Claude?

Sí, mediante el router de proveedores (añadiendo un cliente personalizado).
