# 🧪 Ejemplos de Agentes para NanuCore

Esta carpeta contiene agentes de ejemplo que demuestran diferentes capacidades del framework. Todos son **totalmente funcionales** y pueden usarse como base para crear tus propios agentes.

---

## 📋 Agentes disponibles

### 1. `dev_assistant` - Asistente de Desarrollo
**Descripción:** Herramientas de desarrollo con integración GitHub y revisión de código.

**Capacidades:**
- 📂 Revisión de código (análisis de sintaxis, detección de TODOs, líneas largas)
- 🐙 Gestión de repositorios GitHub (listar repositorios)
- 📝 Creación de issues y pull requests (estructurado)
- 📋 Generación de especificaciones técnicas

**Dependencias:**
pip install PyGithub
export GITHUB_TOKEN=your_token

**Rutas principales:**
- /code_review - Revisar código
- /github - Gestionar repositorios
- /spec_generate - Generar especificaciones

---

### 2. `narrador_dnd` - Dungeon Master

**Descripción:** Director de juego para D&D con gestión de personajes, inventarios y campañas.

**Capacidades:**
- 👤 Creación y visualización de personajes (fichas en Markdown)
- 📦 Gestión de inventarios (tablas Markdown)
- 📖 Gestión de campañas (quests, estado)
- 🎲 Generación de NPCs, encuentros, tesoros y mazmorras
- 🎵 Música de ambientación (Spotify playlists)

**Dependencias:**
pip install pandas openpyxl python-docx beautifulsoup4 lxml

**Rutas principales:**
- /crear_personaje - Crear nuevo personaje
- /mostrar_personaje - Ver ficha del personaje
- /anadir_item - Añadir item al inventario
- /mostrar_inventario - Ver inventario
- /crear_npc - Generar NPC
- /encuentro_combate - Diseñar encuentro
- /mazmorra - Generar mazmorra
- /tesoros - Crear objetos mágicos
- /trama_principal - Generar trama de campaña
- /playlist_fantasia - Música de fantasía

---

### 3. `test_gatekeeper` - Prueba de Gatekeeper

**Descripción:** Agente de prueba para verificar el sistema de aprobación humana.

**Capacidades:**
- 🔐 Prueba de gatekeeper_required: true
- ⏱️ Timeout configurable
- 📝 Logging de decisiones

**Rutas principales:**
- /confirm - Requiere aprobación humana

---

## 🚀 Cómo usar los ejemplos

### 1. Copiar un agente existente

cp -r examples/agents/mi_agente agents/

### 2. Crear un agente desde cero

mkdir -p agents/mi_agente/routes

### 3. Probar un agente

python main.py

---

## 📝 Estructura de un agente

agents/mi_agente/
├── config.yaml        # Configuración del agente
├── routes/            # Rutas YAML
│   ├── accion1.yaml
│   └── accion2.yaml
├── tools/             # Herramientas nativas (scripts)
│   └── mi_tool.py
├── skills/            # Skills específicos (opcional)
└── workspace/         # Datos persistentes (creado automáticamente)

---

## 🔧 Personalización de agentes

### Añadir una nueva ruta

route_id: "mi_ruta"
type: "cognitive"
description: "palabra clave1, palabra clave2"
system_prompt: "Eres un asistente especializado en..."
tools_allowed:
  - mi_herramienta
gatekeeper_required: false

### Añadir una herramienta

import json
import sys

def run(input_data):
    return {"result": "Resultado"}

if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = run(args)
    print(json.dumps(result))

---

## 📚 Recursos adicionales

- Guía de creación de agentes
- API de NanuCore
- README principal

---

## ⚠️ Notas importantes

- Agentes funcionales: Todos los ejemplos son funcionales y pueden usarse directamente.
- Dependencias: Algunos agentes requieren dependencias adicionales (ver requirements-extra.txt).
- Variables de entorno: Configurar .env con las claves API necesarias.
- Seguridad: Revisar las rutas con gatekeeper_required: true para operaciones sensibles.

---

## 🤝 Contribuir

Si creas un agente interesante, ¡considera compartirlo!

- Fork el repositorio
- Añade tu agente en examples/
- Envía un Pull Request con la documentación
