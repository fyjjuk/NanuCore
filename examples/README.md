# Ejemplos y código de referencia

Esta carpeta contiene agentes y herramientas descontinuados que pueden servir como:
- Referencia para crear nuevos agentes
- Inspiración para herramientas personalizadas
- Código legacy preservado con fines educativos

## Agentes de ejemplo:
- `dev_assistant`: Herramientas de GitHub y code review
- `narrador_dnd`: Gestión de personajes e inventarios para D&D
- `test_gatekeeper`: Prueba del sistema de aprobación humana

## Para usar estas herramientas en un agente activo:
1. Copia el código de `tools/` a `agents/tu_agente/tools/`
2. Adapta las rutas YAML a la nueva sintaxis (sin LLM cognitivo innecesario)
3. Actualiza `config.yaml` del agente
