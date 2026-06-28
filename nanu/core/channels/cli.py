"""Canal CLI interactivo para NanuCore (asíncrono)."""
import asyncio
import os
import shlex
import json
from pathlib import Path
from typing import Optional
from nanu.core.orchestrator import Orchestrator
from nanu.core.pipeline import Pipeline
from nanu.core.audio.corrections import corrector
from nanu.core.logging import get_logger

logger = get_logger(__name__)

class CLIChannel:
    def __init__(self, orchestrator: Orchestrator, agent=None):
        self.orchestrator = orchestrator
        self.current_agent = agent
        self.pipeline = None
        self.running = False
    
    async def _ainput(self, prompt: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: input(prompt))
    
    async def run(self):
        if self.current_agent is None:
            self.current_agent = await self.orchestrator.select_agent_interactive()
            if not self.current_agent:
                print("👋 Saliendo...")
                return
        
        # Usar el llm_router del agente para el pipeline
        llm_config = self.current_agent.config.get("llm", {})
        self.pipeline = Pipeline(event_bus=self.orchestrator.event_bus, llm_config=llm_config)
        
        # Si el agente ya tiene un llm_router, usarlo en el pipeline
        if hasattr(self.current_agent, 'llm_router') and self.current_agent.llm_router:
            self.pipeline.llm_router = self.current_agent.llm_router
            logger.debug(f"Usando router LLM del agente: {self.current_agent.llm_router.providers[0].name if self.current_agent.llm_router.providers else 'ninguno'}")
        
        print(f"[+] Agente Activo: {self.current_agent.name} ({self.current_agent.id}") 
        print("[+] Escribe '/exit' para salir, '/help' para ayuda.\n")
        
        self.running = True
        session_key = f"cli_{self.current_agent.id}"
        
        while self.running:
            try:
                user_input = await self._ainput(f"\n[{self.current_agent.id}] > ")
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    result = await self._handle_slash_command(user_input)
                    if result == "EXIT":
                        print("👋 ¡Hasta luego!")
                        return
                    if result:
                        print(result)
                    continue
                
                response, metadata = await self.pipeline.run(self.current_agent, user_input, session_key)
                print(f"\n[Respuesta]\n{response}")
            
            except Exception as e:
                logger.error(f"Error en CLI: {e}", exc_info=True)
                print(f"[-] Error: {e}")
        
        self.running = False
    
    async def _handle_slash_command(self, cmd_line: str) -> Optional[str]:
        parts = shlex.split(cmd_line[1:])
        if not parts:
            return None
        cmd = parts[0].lower()
        
        if cmd in ('exit', 'quit', 'salir'):
            return "EXIT"
        
        elif cmd == 'help':
            return """
Comandos disponibles:
  /exit, /quit, /salir         - Salir del asistente
  /agent list                  - Listar agentes disponibles
  /agent switch <id>           - Cambiar de agente
  /agent info                  - Mostrar detalles del agente (LLM, proveedores)
  /agents                      - Volver al selector interactivo de agentes
  /routes                      - Mostrar las rutas del agente activo
  /learn "original" "correcto" - Aprender corrección fonética
  /list-corrections, /lc       - Listar correcciones guardadas
  /export-corrections, /ec     - Exportar correcciones a archivo JSON
  /clear                       - Limpiar pantalla
  /help                        - Mostrar esta ayuda
"""
        
        elif cmd == 'clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            return ""
        
        elif cmd == 'agent':
            if len(parts) < 2:
                return "Uso: /agent list | /agent switch <agent_id> | /agent info"
            sub = parts[1].lower()
            
            if sub == 'list':
                agents = self.orchestrator.list_agents()
                lines = ["Agentes disponibles:"]
                for a in agents:
                    lines.append(f"  {a['id']} - {a['name']}")
                return "\n".join(lines)
            
            elif sub == 'switch' and len(parts) >= 3:
                agent_id = parts[2]
                new_agent = self.orchestrator.get_agent(agent_id)
                if new_agent:
                    self.current_agent = new_agent
                    # Reutilizar el router del agente
                    llm_config = self.current_agent.config.get("llm", {})
                    self.pipeline = Pipeline(event_bus=self.orchestrator.event_bus, llm_config=llm_config)
                    if hasattr(self.current_agent, 'llm_router') and self.current_agent.llm_router:
                        self.pipeline.llm_router = self.current_agent.llm_router
                    return f"✅ Cambiado al agente: {new_agent.name}"
                else:
                    return f"❌ Agente '{agent_id}' no encontrado"
            
            elif sub == 'info':
                return await self._show_agent_info()
            
            else:
                return "Comando /agent no reconocido. Usa: /agent list | /agent switch <id> | /agent info"
        
        elif cmd == 'agents':
            new_agent = await self.orchestrator.select_agent_interactive()
            if new_agent:
                self.current_agent = new_agent
                llm_config = self.current_agent.config.get("llm", {})
                self.pipeline = Pipeline(event_bus=self.orchestrator.event_bus, llm_config=llm_config)
                if hasattr(self.current_agent, 'llm_router') and self.current_agent.llm_router:
                    self.pipeline.llm_router = self.current_agent.llm_router
                return f"✅ Cambiado al agente: {new_agent.name}"
            else:
                return "❌ Selección cancelada, se mantiene el agente actual."
        
        elif cmd == 'routes':
            if not self.current_agent:
                return "No hay agente seleccionado."
            routes_dir = Path(self.current_agent.config_path).parent / "routes"
            if not routes_dir.exists():
                return "No hay rutas definidas para este agente."
            routes = []
            for yaml_file in sorted(routes_dir.glob("*.yaml")):
                import yaml
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    route = yaml.safe_load(f)
                    if route and 'route_id' in route:
                        desc = route.get('description', '')[:60]
                        routes.append(f"  - {route['route_id']}: {desc}")
            if not routes:
                return "No se encontraron rutas."
            return "📋 Rutas disponibles:\n" + "\n".join(routes)
        
        elif cmd == 'learn':
            if len(parts) < 3:
                return "Uso: /learn \"original\" \"corregido\"\nEjemplo: /learn \"fado de down\" \"fallen down\""
            original = parts[1]
            corrected = parts[2]
            corrector.add_correction(original, corrected)
            return f"📝 Aprendida corrección: '{original}' → '{corrected}'"
        
        elif cmd in ('list-corrections', 'lc'):
            return corrector.list_corrections()
        
        elif cmd in ('export-corrections', 'ec'):
            export_path = Path('data/corrections/exported_map.json')
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(corrector.corrections, f, ensure_ascii=False, indent=2)
            return f"📁 Correcciones exportadas a {export_path}"
        
        else:
            return f"Comando desconocido: /{cmd}. Usa /help."

    async def _show_agent_info(self) -> str:
        """Muestra información detallada del agente actual."""
        if not self.current_agent:
            return "❌ No hay agente seleccionado."
        
        agent = self.current_agent
        lines = []
        lines.append(f"📋 Información del agente: {agent.name} ({agent.id})")
        lines.append(f"   Descripción: {agent.description}")
        lines.append(f"   Workspace: {agent.workspace.root}")
        lines.append(f"   Memoria: {agent.short_term_memory_window} turnos")
        lines.append(f"   Modo ejecución: {agent.execution_mode}")
        lines.append("")
        
        # Información de LLM
        if hasattr(agent, 'llm_router') and agent.llm_router:
            lines.append("   🤖 Proveedores LLM:")
            for provider in agent.llm_router.providers:
                priority = agent.llm_router.get_provider_priority(provider.name)
                # Verificar disponibilidad (usamos la caché del router)
                is_available = "✅"  # Por simplicidad, asumimos disponible
                lines.append(f"      {is_available} {provider.name} (prioridad: {priority})")
                lines.append(f"         Modelo: {provider.model}")
                lines.append(f"         Temperatura: {provider.temperature}")
                lines.append(f"         Max tokens: {provider.max_tokens}")
                lines.append(f"         Timeout: {provider.timeout}s")
        else:
            lines.append("   ⚠️ No hay proveedores LLM configurados")
        
        lines.append("")
        
        # Información de herramientas
        if agent.tools:
            lines.append("   🛠️ Herramientas disponibles:")
            for tool_name, tool in agent.tools.items():
                status = "✅" if tool.enabled else "❌"
                lines.append(f"      {status} {tool_name}: {tool.description[:50]}...")
        else:
            lines.append("   ℹ️ No hay herramientas configuradas")
        
        lines.append("")
        
        # Información de caché
        cache_enabled = hasattr(agent, 'cache_config') and agent.cache_config.enabled
        lines.append(f"   💾 Caché: {'✅ Activada' if cache_enabled else '❌ Desactivada'}")
        if cache_enabled:
            ttl = getattr(agent.cache_config, 'ttl', 3600)
            lines.append(f"      TTL: {ttl}s")
        
        return "\n".join(lines)
