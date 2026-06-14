"""Canal CLI interactivo para NanuCore (asíncrono)."""
import asyncio
import os
from pathlib import Path
from typing import Optional
from nanu.core.orchestrator import Orchestrator
from nanu.core.pipeline import Pipeline

class CLIChannel:
    def __init__(self, orchestrator: Orchestrator, agent=None):
        self.orchestrator = orchestrator
        self.current_agent = agent
        self.pipeline = None  # Se inicializará en run() con el agente
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
        
        # Inicializar pipeline con la configuración LLM del agente
        llm_config = self.current_agent.config.get("llm", {})
        self.pipeline = Pipeline(event_bus=self.orchestrator.event_bus, llm_config=llm_config)
        
        print(f"[+] Agente Activo: {self.current_agent.name} ({self.current_agent.id})")
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
                print(f"[-] Error: {e}")
        
        self.running = False
    
    async def _handle_slash_command(self, cmd_line: str) -> Optional[str]:
        parts = cmd_line.split()
        cmd = parts[0].lower()
        
        if cmd in ('/exit', '/quit', '/salir'):
            return "EXIT"
        elif cmd == '/help':
            return """
Comandos disponibles:
  /exit, /quit, /salir - Salir del asistente
  /agent list          - Listar agentes disponibles
  /agent switch <id>   - Cambiar de agente
  /agents              - Volver al selector interactivo de agentes
  /routes              - Mostrar las rutas del agente activo
  /clear               - Limpiar pantalla
  /help                - Mostrar esta ayuda
"""
        elif cmd == '/clear':
            os.system('clear' if os.name == 'posix' else 'cls')
            return ""
        elif cmd == '/agent':
            if len(parts) < 2:
                return "Uso: /agent list | /agent switch <agent_id>"
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
                    # Recrear pipeline con nueva configuración
                    llm_config = self.current_agent.config.get("llm", {})
                    self.pipeline = Pipeline(event_bus=self.orchestrator.event_bus, llm_config=llm_config)
                    return f"✅ Cambiado al agente: {new_agent.name}"
                else:
                    return f"❌ Agente '{agent_id}' no encontrado"
            else:
                return "Comando /agent no reconocido"
        elif cmd == '/agents':
            new_agent = await self.orchestrator.select_agent_interactive()
            if new_agent:
                self.current_agent = new_agent
                llm_config = self.current_agent.config.get("llm", {})
                self.pipeline = Pipeline(event_bus=self.orchestrator.event_bus, llm_config=llm_config)
                return f"✅ Cambiado al agente: {new_agent.name}"
            else:
                return "❌ Selección cancelada, se mantiene el agente actual."
        elif cmd == '/routes':
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
        else:
            return f"Comando desconocido: {cmd}. Usa /help."
