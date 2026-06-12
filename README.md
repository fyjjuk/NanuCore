# NanuCore - Asistente Personal Multi-Agente con IA

**Versión:** 3.0.0 (Python 3.11, versión limpia)  
**Estado:** Producción estable | **Arquitectura:** Hexagonal + Plugins

## Descripción General

NanuCore (anteriormente FerdoNAN) es un framework modular para asistentes de IA basado en agentes especializados, con soporte de voz integrado, enrutamiento de intenciones y ejecución segura.

## Características

- **Múltiples agentes**: Spotify Controller, Narrador D&D, Developer Assistant, fácilmente extensible.
- **Asistente de voz** (opcional): STT offline con Vosk, TTS natural con edge-tts, hotkey con tecla Copilot.
- **Comandos slash**: `/help`, `/exit`, `/agent`, `/agent list`, `/agent switch`, `/config show`, `/clear`.
- **Seguridad multicapa**: Ingress filter, Egress filter, Gatekeeper con aprobación humana.
- **CLI interactiva**: Historial, autocompletado, temas visuales (Refero, Cyberpunk).

## Requisitos

- Python 3.11 (recomendado)
- Ollama (opcional, para agentes que usen LLM local)
- mpg123 (para voz, solo si se activa edge-tts)

## Instalación rápida

```bash
git clone https://github.com/fyjjuk/NanuCore.git
cd NanuCore
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Configuración

Copia `.env.example` a `.env` y completa tus API keys (si usas Gemini, Groq).

```bash
cp .env.example .env
```

## Comandos CLI

| Comando | Descripción |
|---|---|
| `/help` | Muestra la ayuda |
| `/exit` o `/quit` | Sale del asistente |
| `/agent` | Abre selector interactivo de agentes |
| `/agent list` | Lista agentes disponibles |
| `/agent switch <nombre>` | Cambia al agente especificado |
| `/config show` | Muestra configuración actual |
| `/clear` | Limpia la pantalla |

## Voz (opcional)

Para activar el asistente de voz:

```bash
export FERDONAN_VOICE_ENABLED=true
python main.py
```

- Presiona la tecla Copilot para iniciar/detener grabación (modo toggle).
- Necesita mpg123: `sudo dnf install mpg123` (Fedora) o equivalente.

## Estructura del proyecto

```
NanuCore/
├── agents/          # Agentes especializados
├── core/            # Orquestador, pipeline, interfaces
├── services/        # Router, sanitizer, voice, llm_providers
├── security/        # Firewalls, gatekeeper, rate limiter
├── ui/              # CLI, comandos slash, selector de agentes
├── models/          # Pydantic models
├── persistence/     # Memoria corto y largo plazo
├── main.py          # Punto de entrada
└── requirements.txt # Dependencias mínimas
```

## Licencia

MIT
