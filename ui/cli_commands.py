"""Comandos CLI reutilizables para FerdoNAN."""

import os
from config.settings import settings


def cmd_help():
    return """
Comandos disponibles:
  /exit, /quit               - Salir del asistente
  /agent                     - Abrir selector interactivo de agentes
  /agent list                - Listar agentes disponibles
  /agent switch <nombre>     - Cambiar al agente especificado (por ID o nombre)
  /config show               - Mostrar configuración actual
  /clear                     - Limpiar la pantalla
  /help                      - Mostrar esta ayuda
"""


def cmd_agent_list(agents):
    lines = ["\n📋 Agentes disponibles:"]
    for aid, a in agents.items():
        lines.append(f"  • {a.name} (ID: {aid})")
    return "\n".join(lines)


def cmd_agent_switch(arg, current_agent, agents):
    if not arg:
        return "❌ Uso: /agent switch <nombre> o <ID>", current_agent
    for aid, a in agents.items():
        if aid == arg or a.name.lower() == arg.lower():
            return f"✅ Cambiado al agente: {a.name} ({aid})", a
    return f"❌ Agente '{arg}' no encontrado. Usa /agent list para ver disponibles.", current_agent


def cmd_config_show():
    theme = os.environ.get("FERDONAN_THEME", "refero")
    locale = os.environ.get("FERDONAN_LOCALE", "en")
    return f"""
Configuración actual:
  Tema: {theme}
  Idioma: {locale}
  Ollama host: {settings.OLLAMA_HOST}
  Gatekeeper timeout: {settings.GATEKEEPER_TIMEOUT}s
  Rate limit: {settings.RATE_LIMIT_MAX_REQUESTS} req/{settings.RATE_LIMIT_WINDOW_SECONDS}s
"""


def cmd_clear():
    os.system('clear' if os.name == 'posix' else 'cls')
    return ""


def process_slash_command(user_input, agents, current_agent):
    """Procesa un comando slash y retorna (mensaje, nuevo_agente, debe_salir)."""
    parts = user_input.split()
    cmd = parts[0].lower()
    
    if cmd in ('/exit', '/quit'):
        return "👋 ¡Hasta luego!", current_agent, True
    elif cmd == '/help':
        return cmd_help(), current_agent, False
    elif cmd == '/agent':
        if len(parts) == 1:
            # Solo /agent -> abrir selector interactivo
            from ui.agent_selector import select_agent_interactive
            print("\n🔄 Abriendo selector de agentes...")
            new_agent = select_agent_interactive(agents)
            if new_agent is None:
                return "👋 Selección cancelada.", current_agent, False
            return f"✅ Cambiado al agente: {new_agent.name}", new_agent, False
        elif len(parts) >= 2:
            sub = parts[1].lower()
            if sub == 'list':
                return cmd_agent_list(agents), current_agent, False
            elif sub == 'switch':
                arg = parts[2] if len(parts) > 2 else None
                msg, new_agent = cmd_agent_switch(arg, current_agent, agents)
                return msg, new_agent, False
            else:
                return f"❌ Subcomando desconocido: {sub}", current_agent, False
    elif cmd == '/config' and len(parts) > 1 and parts[1].lower() == 'show':
        return cmd_config_show(), current_agent, False
    elif cmd == '/clear':
        return cmd_clear(), current_agent, False
    else:
        return f"❌ Comando desconocido: {cmd}. Usa /help.", current_agent, False
