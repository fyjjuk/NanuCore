# Guía de Creación de Agentes

## Estructura básica de un agente

```
agents/mi_agente/
├── config.yaml        # Configuración del agente
├── routes/            # Rutas YAML
│   ├── accion1.yaml
│   └── accion2.yaml
├── tools/             # Herramientas nativas (scripts)
│   └── mi_herramienta.py
├── skills/            # Skills específicos del agente
└── workspace/         # Datos persistentes (creado automáticamente)
```

## Paso 1: Crear config.yaml

```yaml
id: "mi_agente"
name: "Mi Agente"
description: "Descripción de mi agente"
workspace: "workspace/mi_agente"
short_term_memory_window: 10
execution_mode: "parallel"
llm_provider:
  name: "ollama"
  model: "llama3.2:3b"
  light_model: "phi3:mini"
  heavy_model: "llama3.2:3b"
  temperature: 0.7
  max_tokens: 4096
tools:
  native:
    - name: "mi_herramienta"
      script: "tools/mi_herramienta.py"
      enabled: true
cache:
  enabled: true
  ttl: 3600
router_config:
  mode: "keyword"
  threshold: 0.2
```

## Paso 2: Definir rutas

### Ruta tipo Script (ejecuta una herramienta)

```yaml
# routes/mi_accion.yaml
route_id: "mi_accion"
type: "script"
description: "palabra clave1, palabra clave2, acción específica"
script_path: "tools/mi_herramienta.py"
script_args:
  action: "mi_accion"
  param: "{user_input}"
gatekeeper_required: false
```

### Ruta tipo Cognitive (usa LLM)

```yaml
# routes/mi_pregunta.yaml
route_id: "mi_pregunta"
type: "cognitive"
description: "pregunta, consulta, información"
system_prompt: |
  Eres un asistente especializado en...
  Responde de manera útil y concisa.
tools_allowed:
  - mi_herramienta
gatekeeper_required: false
```

## Paso 3: Crear herramientas

```python
# tools/mi_herramienta.py
import json
import sys
from typing import Dict, Any

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    action = input_data.get("action", "")

    if action == "mi_accion":
        param = input_data.get("param", "")
        result = f"Procesado: {param}"
    else:
        result = "Acción desconocida"

    return {"result": result}

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))
```

## Paso 4: Probar el agente

```bash
python main.py
# Seleccionar "Mi Agente"
# Probar los comandos definidos en las rutas
```

## Uso de placeholders en script_args

```yaml
script_args:
  action: "add"
  character: "{user_input}"    # Toda la entrada del usuario
  item: "poción"
  quantity: 1
```

## Herramientas con clase Tool (avanzado)

```python
from nanu.core.interfaces import Tool

class MiHerramienta(Tool):
    name = "mi_herramienta"
    description = "Mi herramienta personalizada"
    enabled = True

    async def execute(self, args: Dict[str, Any], workspace=None) -> str:
        action = args.get("action", "")
        if action == "saludar":
            return f"Hola, {args.get('nombre', 'mundo')}!"
        return "Acción desconocida"
```

## Skills reutilizables

Crear un skill en `nanu/skills/mi_skill/`:

```yaml
# skill.yaml
name: "Mi Skill"
description: "Habilidades reutilizables"
version: "1.0.0"
```

```python
# tools/mi_skill_tool.py
from nanu.core.interfaces import Tool

class MiSkillTool(Tool):
    name = "mi_skill_tool"
    description = "Herramienta del skill"
    enabled = True

    async def execute(self, args: Dict[str, Any], workspace=None) -> str:
        return "Ejecutando skill..."
```

## Tips y buenas prácticas

- **Descripciones ricas en keywords**: Para mejor enrutamiento, incluye sinónimos en la descripción.
- **Umbral de routing**: Ajusta `threshold` en `router_config` según la precisión deseada.
- **Gatekeeper**: Usa `gatekeeper_required: true` para operaciones críticas.
- **Caché**: Habilita caché para rutas cognitivas repetitivas.
- **Workspace**: Cada agente tiene su propio sandbox para datos persistentes.
