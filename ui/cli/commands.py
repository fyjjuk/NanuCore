"""
Sistema de comandos para FerdoNAN CLI.
Soporta comandos slash (/comando) para controlar el asistente.
"""

from typing import Dict, Callable, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import shlex


class CommandCategory(Enum):
    """Categorías de comandos."""
    SYSTEM = "system"
    AGENT = "agent"
    HELP = "help"
    CONFIG = "config"
    DEBUG = "debug"


@dataclass
class Command:
    """Definición de un comando CLI."""
    name: str
    handler: Callable
    description: str
    category: CommandCategory
    aliases: List[str] = None
    usage: str = ""
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []


class CommandRegistry:
    """Registro central de comandos CLI."""
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._history: List[str] = []
        self._history_file = ".ferdonan_history"
        self._load_history()
    
    def register(self, command: Command) -> None:
        """Registra un nuevo comando."""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command
    
    def get_command(self, cmd_name: str) -> Optional[Command]:
        """Obtiene un comando por nombre o alias."""
        return self._commands.get(cmd_name)
    
    def execute(self, cmd_line: str, **kwargs) -> str:
        """
        Ejecuta un comando.
        
        Args:
            cmd_line: Línea de comando completa (ej. "/agent list")
            **kwargs: Argumentos adicionales para el handler
            
        Returns:
            str: Resultado del comando
        """
        if not cmd_line.startswith('/'):
            return None
        
        # Parsear comando
        parts = shlex.split(cmd_line[1:])  # Remover el '/'
        cmd_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # Guardar en historial
        self._add_to_history(cmd_line)
        
        # Buscar comando
        cmd = self.get_command(cmd_name)
        if not cmd:
            return f"Comando desconocido: /{cmd_name}. Use /help para ver comandos disponibles."
        
        # Ejecutar handler
        try:
            return cmd.handler(args, **kwargs)
        except Exception as e:
            return f"Error ejecutando comando: {e}"
    
    def _add_to_history(self, cmd_line: str) -> None:
        """Añade comando al historial."""
        self._history.append(cmd_line)
        # Mantener solo últimos 1000 comandos
        if len(self._history) > 1000:
            self._history = self._history[-1000:]
        self._save_history()
    
    def _load_history(self) -> None:
        """Carga historial desde archivo."""
        try:
            with open(self._history_file, 'r') as f:
                self._history = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            pass
    
    def _save_history(self) -> None:
        """Guarda historial a archivo."""
        try:
            with open(self._history_file, 'w') as f:
                f.write('\n'.join(self._history[-500:]))
        except Exception:
            pass
    
    def get_history(self, limit: int = 50) -> List[str]:
        """Retorna historial de comandos."""
        return self._history[-limit:]
    
    def suggest(self, partial: str) -> List[str]:
        """Sugiere comandos que coinciden con el prefijo."""
        partial = partial.lstrip('/').lower()
        return [f"/{cmd}" for cmd in self._commands.keys() 
                if cmd.startswith(partial) and not cmd.startswith('/')]
    
    def list_commands(self, category: CommandCategory = None) -> Dict[str, Command]:
        """Lista comandos por categoría."""
        if category:
            return {name: cmd for name, cmd in self._commands.items() 
                    if cmd.category == category}
        return self._commands.copy()


# Comandos predefinidos
def _cmd_help(args: List[str], **kwargs) -> str:
    """Muestra ayuda de comandos."""
    ui = kwargs.get('ui')
    registry = kwargs.get('registry')
    
    if not registry:
        return "Sistema de ayuda no disponible"
    
    lines = ["Comandos disponibles:"]
    lines.append("")
    
    for category in CommandCategory:
        cmds = registry.list_commands(category)
        if cmds:
            category_name = category.value.upper()
            lines.append(f"📁 {category_name}")
            for name, cmd in cmds.items():
                if not name.startswith('/'):  # Evitar duplicados por alias
                    desc = cmd.description[:50] + "..." if len(cmd.description) > 50 else cmd.description
                    usage = f" /{name} {cmd.usage}".strip() if cmd.usage else f" /{name}"
                    lines.append(f"  {usage:<25} - {desc}")
            lines.append("")
    
    lines.append("💡 Tips:")
    lines.append("  - Use TAB para autocompletar comandos")
    lines.append("  - Use ↑/↓ para navegar en el historial")
    lines.append("  - Escriba directamente para hablar con el asistente")
    
    return "\n".join(lines)


def _cmd_exit(args: List[str], **kwargs) -> str:
    """Sale del asistente."""
    return "EXIT"


def _cmd_clear(args: List[str], **kwargs) -> str:
    """Limpia la pantalla."""
    import os
    os.system('clear' if os.name == 'posix' else 'cls')
    return "CLEAR"


def _cmd_agent_list(args: List[str], **kwargs) -> str:
    """Lista agentes disponibles."""
    agents = kwargs.get('agents', {})
    ui = kwargs.get('ui')
    
    if not agents:
        return "No hay agentes disponibles"
    
    lines = ["Agentes disponibles:"]
    lines.append("")
    
    for agent_id, manifest in agents.items():
        status = "✅" if hasattr(manifest, 'llm_client') and manifest.llm_client else "⚠️"
        lines.append(f"  {status} {agent_id:<20} - {manifest.description[:50]}")
    
    return "\n".join(lines)


def _cmd_agent_select(args: List[str], **kwargs) -> str:
    """Selecciona un agente activo."""
    agents = kwargs.get('agents', {})
    current_agent = kwargs.get('current_agent')
    
    if not args:
        return f"Agente actual: {current_agent.id if current_agent else 'ninguno'}"
    
    agent_name = args[0]
    if agent_name in agents:
        return f"SELECT_AGENT:{agent_name}"
    else:
        return f"Agente '{agent_name}' no encontrado. Use /agent list para ver disponibles."


def _cmd_config_show(args: List[str], **kwargs) -> str:
    """Muestra configuración actual."""
    settings = kwargs.get('settings')
    ui = kwargs.get('ui')
    
    lines = ["Configuración actual:"]
    lines.append("")
    lines.append(f"  Tema: {getattr(settings, 'FERDONAN_THEME', 'refero')}")
    lines.append(f"  Idioma: {getattr(settings, 'FERDONAN_LOCALE', 'en')}")
    lines.append(f"  Ollama: {getattr(settings, 'OLLAMA_HOST', 'localhost:11434')}")
    
    return "\n".join(lines)


def _cmd_debug_info(args: List[str], **kwargs) -> str:
    """Muestra información de depuración."""
    import sys
    import platform
    
    lines = ["Información de depuración:"]
    lines.append("")
    lines.append(f"  Python: {platform.python_version()}")
    lines.append(f"  OS: {platform.system()} {platform.release()}")
    lines.append(f"  FerdoNAN: {getattr(kwargs.get('settings'), 'VERSION', '2.4.0')}")
    
    return "\n".join(lines)


def create_default_registry() -> CommandRegistry:
    """Crea registro de comandos con comandos por defecto."""
    registry = CommandRegistry()
    
    # Comandos de ayuda
    registry.register(Command(
        name="help",
        handler=_cmd_help,
        description="Muestra esta ayuda",
        category=CommandCategory.HELP,
        aliases=["h", "?"],
        usage="[comando]"
    ))
    
    # Comandos de sistema
    registry.register(Command(
        name="exit",
        handler=_cmd_exit,
        description="Sale del asistente",
        category=CommandCategory.SYSTEM,
        aliases=["quit", "q"],
        usage=""
    ))
    
    registry.register(Command(
        name="clear",
        handler=_cmd_clear,
        description="Limpia la pantalla",
        category=CommandCategory.SYSTEM,
        aliases=["cls"],
        usage=""
    ))
    
    # Comandos de agente
    registry.register(Command(
        name="agent",
        handler=_cmd_agent_list,
        description="Gestiona agentes (list, select)",
        category=CommandCategory.AGENT,
        usage="[list|select <nombre>]"
    ))
    
    # Comandos de configuración
    registry.register(Command(
        name="config",
        handler=_cmd_config_show,
        description="Muestra configuración",
        category=CommandCategory.CONFIG,
        usage="[show]"
    ))
    
    # Comandos de depuración
    registry.register(Command(
        name="debug",
        handler=_cmd_debug_info,
        description="Información de depuración",
        category=CommandCategory.DEBUG,
        aliases=["info"],
        usage=""
    ))
    
    return registry
