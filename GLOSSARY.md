# Glosario de términos - FerdoNAN

## Arquitectura de directorios (post-refactorización)

```
ferdonan/
├── agents/                     # Agentes especializados
│   ├── narrador_dnd/           # Director de juego D&D
│   │   ├── resources/          # Inmutable (libros, reglas)
│   │   ├── workspace/          # Editable (personajes, inventarios)
│   │   ├── tools/              # Herramientas del agente
│   │   └── routes/             # YAML de intenciones
│   ├── spotify_player/         # Control de Spotify
│   └── dev_assistant/          # GitHub + code review
├── core/                       # Núcleo del sistema
│   ├── orchestrator.py         # Coordina el pipeline (antes engine.py)
│   ├── processor.py            # Pipeline de procesamiento
│   ├── component_factory.py    # Crea routers y sanitizers
│   ├── llm_client_factory.py   # Crea clientes LLM
│   ├── interfaces.py           # Protocolos y ABCs
│   └── i18n/                   # Localización
├── services/                   # Servicios
│   ├── executor/               # Ejecutores de intenciones
│   │   ├── llm_executor.py     # Usa LLM (antes cognitive.py)
│   │   ├── script_executor.py  # Ejecuta scripts
│   │   ├── stage_executor.py   # Ejecuta stages multi-LLM
│   │   └── factory.py          # Fábrica de ejecutores
│   ├── router/                 # Enrutamiento de intenciones
│   ├── sanitizer/              # Limpieza de entrada
│   ├── llm_providers/          # Clientes LLM
│   └── rag/                    # RAG modular
├── security/                   # Seguridad
│   ├── filters/                # Ingress, egress, semántico
│   ├── auth/                   # Gatekeeper, auditoría
│   └── rate_limiter.py
├── ui/                         # Interfaz de usuario
│   ├── agent_selector.py       # Selección interactiva de agente
│   ├── cli_commands.py         # Comandos slash reutilizables
│   ├── console/                # Renderer ANSI
│   └── ascii/                  # Componentes ASCII
├── models/                     # Modelos de datos
│   ├── agent_manifest.py       # Esquema de agente
│   └── route_models.py         # Esquemas de rutas
├── tests/                      # Pruebas unitarias
├── libs/                       # Bibliotecas de ejemplo
└── docs/                       # Documentación Sphinx
```

## Convenciones de nombres

| Elemento | Convención | Ejemplo |
|---|---|---|
| Archivo de agente | `{nombre}.yaml` | `crear_personaje.yaml` |
| Herramienta de agente | `{nombre}_manager.py` | `inventory_manager.py` |
| Clase ejecutora | `{tipo}Executor` | `LLMExecutor`, `ScriptExecutor` |
| Fábrica | `{recurso}Factory` | `ComponentFactory` |
| Cliente | `{proveedor}Client` | `OllamaClient` |

## Variables clave

| Variable | Significado |
|---|---|
| `agent` | Instancia de un agente |
| `intent` | Ruta seleccionada (antes `intent`) |
| `query` | Entrada del usuario saneada (antes `query`) |
| `available_tools` | Herramientas que el agente puede usar |
| `orchestrator` | Coordinador principal (antes `engine`) |

## Cómo usar este glosario

1. Los LLM deben leer este archivo como contexto antes de analizar el código.
2. Los nuevos desarrolladores deben consultarlo para entender la nomenclatura.
3. Al añadir nuevos componentes, seguir las convenciones aquí definidas.
