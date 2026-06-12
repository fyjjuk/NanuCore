import yaml
from pathlib import Path
from typing import Dict, Optional, List
from nanu.core.agent import Agent
from nanu.core.memory.jsonl import JSONLMemory
from nanu.core.memory.vector import SQLiteVectorStore
from nanu.core.providers.factory import create_llm_client
from nanu.core.tools.registry import ToolRegistry
from nanu.core.events.bus import EventBus
from nanu.core.skills.loader import SkillLoader
from nanu.core.security.gatekeeper import Gatekeeper

class Orchestrator:
    def __init__(self, agents_dir: str = "agents", data_dir: str = "nanu/data"):
        self.agents_dir = Path(agents_dir)
        self.data_dir = Path(data_dir)
        self.agents: Dict[str, Agent] = {}
        self.memory = JSONLMemory(str(self.data_dir / "sessions"))
        self.vector_store = SQLiteVectorStore(str(self.data_dir / "vectors.db"))
        self.tool_registry = ToolRegistry()
        self.event_bus = EventBus()
        self.skill_loader = SkillLoader()
        self.gatekeeper = Gatekeeper(default_timeout=60, force_all=False, session_ttl=300)
    
    async def load_agents(self) -> None:
        if not self.tool_registry.list():
            self.tool_registry.register_builtin()
        
        if not self.agents_dir.exists():
            self.agents_dir.mkdir(parents=True)
            return
        
        for agent_dir in self.agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            config_path = agent_dir / "config.yaml"
            if not config_path.exists():
                continue
            
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
            
            # Crear clientes LLM
            llm_clients = {}
            light_cfg = cfg.get('llm_provider', {}).copy()
            light_cfg['model'] = light_cfg.get('light_model', light_cfg.get('model', 'phi3:mini'))
            llm_clients['light'] = create_llm_client(light_cfg)
            
            heavy_cfg = cfg.get('llm_provider', {}).copy()
            heavy_cfg['model'] = heavy_cfg.get('heavy_model', heavy_cfg.get('model', 'llama3.2:3b'))
            llm_clients['heavy'] = create_llm_client(heavy_cfg)
            
            # Cargar herramientas nativas del agente
            tools = []
            for tool_cfg in cfg.get('tools', {}).get('native', []):
                tool_name = tool_cfg['name']
                builtin_tool = self.tool_registry.get(tool_name)
                if builtin_tool and builtin_tool.enabled:
                    tools.append(builtin_tool)
            
            # Cargar skills
            skill_tools = self.skill_loader.load_skills_for_agent(agent_dir)
            tools.extend(skill_tools)
            
            agent = Agent(
                config_path=str(config_path),
                llm_clients=llm_clients,
                tools=tools,
                memory=self.memory,
                vector_store=self.vector_store
            )
            # Asignar gatekeeper al agente
            agent.gatekeeper = self.gatekeeper
            self.agents[agent.id] = agent
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[Dict[str, str]]:
        return [{"id": a.id, "name": a.name, "description": a.description} 
                for a in self.agents.values()]
    
    async def select_agent_interactive(self) -> Optional[Agent]:
        agents_list = list(self.agents.values())
        if not agents_list:
            print("No hay agentes disponibles.")
            return None
        
        print("\n" + "="*60)
        print("🎮 SELECCIÓN DE AGENTE")
        print("="*60)
        for i, agent in enumerate(agents_list, 1):
            print(f"  {i}. {agent.name} (ID: {agent.id})")
        print("  0. Salir")
        print("="*60)
        
        while True:
            try:
                choice = input("\n👉 Elige un número: ").strip()
                if choice == "0":
                    return None
                idx = int(choice) - 1
                if 0 <= idx < len(agents_list):
                    return agents_list[idx]
                print(f"❌ Opción inválida. Elige entre 1 y {len(agents_list)}")
            except ValueError:
                print("❌ Por favor, ingresa un número válido")
            except KeyboardInterrupt:
                print("\n👋 Saliendo...")
                return None
