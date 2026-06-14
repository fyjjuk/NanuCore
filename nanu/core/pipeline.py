from pathlib import Path
import asyncio
import subprocess
import json
import re
from typing import Dict, Any, Tuple, Optional
from nanu.core.agent import Agent
from nanu.core.routing.intent_router import IntentRouter
from nanu.core.routing.model_router import ModelRouter
from nanu.core.events.bus import EventBus
from nanu.core.events.hooks import HookManager
from nanu.core.cache import DiskCache
from nanu.core.providers import create_llm_router
from nanu.core.corrections import corrector

class Pipeline:
    def __init__(self, event_bus: Optional[EventBus] = None, llm_config: Optional[Dict] = None):
        self.event_bus = event_bus or EventBus()
        self.intent_router = IntentRouter()
        self.model_router = ModelRouter()
        self.cache = DiskCache()
        self.hook_manager = HookManager()
        self.llm_router = create_llm_router(llm_config or {})
    
    def get_hook_manager(self) -> HookManager:
        return self.hook_manager
    
    async def run(self, agent: Agent, user_input: str, session_key: str) -> Tuple[str, Dict[str, Any]]:
        context = {"agent": agent, "session_key": session_key}
        
        # Aplicar correcciones fonéticas al input
        corrected_input = corrector.correct(user_input)
        if corrected_input != user_input:
            print(f"🔧 Corrección aplicada: '{user_input}' → '{corrected_input}'")
        
        processed_input = await self.hook_manager.run_pre_hooks(corrected_input, context)
        sanitized = processed_input.strip()
        if not sanitized:
            return "No se detectó entrada.", {"route_id": "none", "model": "none"}
        
        await self.event_bus.publish("pipeline.sanitized", {"input": sanitized})
        
        if self._is_blocked(sanitized):
            return "Entrada bloqueada por políticas de seguridad.", {"route_id": "blocked"}
        
        routed_input = await self.hook_manager.run_pre_route_hooks(sanitized, context)
        route = self.intent_router.route(agent, routed_input)
        
        if not route:
            return "No se pudo determinar la intención.", {"route_id": "unknown"}
        
        route_id = await self.hook_manager.run_post_route_hooks(route['route_id'], routed_input, context)
        if route_id != route['route_id']:
            route = agent.get_route(route_id) or route
        
        await self.event_bus.publish("pipeline.routed", {"route_id": route['route_id']})
        
        if hasattr(agent, 'gatekeeper') and agent.gatekeeper:
            approved = await agent.gatekeeper.verify(route['route_id'], route, session_key, session_key)
            if not approved:
                return "Acción rechazada por Gatekeeper.", {"route_id": route['route_id'], "blocked": True}
        
        route_type = route.get('type', 'cognitive')
        try:
            if route_type == 'script':
                response = await self._execute_script(agent, route, sanitized)
            else:
                cache_enabled = hasattr(agent, 'cache_config') and agent.cache_config.enabled
                cached = None
                if cache_enabled:
                    system_prompt = route.get('system_prompt', "")
                    cached = self.cache.get(agent.id, route['route_id'], sanitized, system_prompt)
                if cached:
                    response = cached
                    await self.event_bus.publish("pipeline.cache_hit", {"route_id": route['route_id']})
                else:
                    response = await self._execute_cognitive(agent, route, sanitized)
                    if cache_enabled:
                        ttl = getattr(agent.cache_config, 'ttl', 3600)
                        system_prompt = route.get('system_prompt', "")
                        self.cache.set(agent.id, route['route_id'], sanitized, response, system_prompt, ttl)
                response = await self._handle_tool_calls(agent, response)
            
            if self._is_egress_blocked(response):
                response = "La respuesta fue bloqueada por políticas de seguridad."
            
            response = await self.hook_manager.run_post_hooks(response, context)
            
        except Exception as e:
            await self.hook_manager.run_error_hooks(e, sanitized, context)
            return f"Error en pipeline: {e}", {"route_id": route['route_id'], "error": str(e)}
        
        await agent.memory.add(session_key, {"role": "user", "content": sanitized, "timestamp": None})
        await agent.memory.add(session_key, {"role": "assistant", "content": response, "timestamp": None})
        
        metadata = {"route_id": route['route_id'], "execution_mode": agent.execution_mode}
        await self.event_bus.publish("pipeline.completed", {"response": response, "metadata": metadata})
        return response, metadata
    
    def _is_blocked(self, text: str) -> bool:
        blocked = ["rm -rf", "sudo", "passwd"]
        for pattern in blocked:
            if pattern in text.lower():
                return True
        return False
    
    def _is_egress_blocked(self, text: str) -> bool:
        dangerous = ["rm", "curl", "wget"]
        for cmd in dangerous:
            if f" {cmd} " in f" {text} " or text.startswith(f"{cmd} "):
                return True
        return False
    
    async def _execute_script(self, agent: Agent, route: Dict, user_input: str) -> str:
        script_path = route.get('script_path')
        if not script_path:
            return "Error: script_path no definido"
        agent_dir = Path(agent.config_path).parent
        full_script = agent_dir / script_path
        if not full_script.exists():
            return f"Error: herramienta no encontrada: {script_path}"
        args = route.get('script_args', {})
        processed = {}
        for k, v in args.items():
            if isinstance(v, str) and "{user_input}" in v:
                processed[k] = v.replace("{user_input}", user_input)
            else:
                processed[k] = v
        try:
            result = subprocess.run(
                ["python", str(full_script), json.dumps(processed)],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr}"
        except Exception as e:
            return f"Error ejecutando script: {e}"
    
    async def _execute_cognitive(self, agent: Agent, route: Dict, user_input: str) -> str:
        system_prompt = route.get('system_prompt', "Eres un asistente útil.")
        if route.get('tools_allowed'):
            tools_desc = "\nHerramientas disponibles: " + ", ".join(route['tools_allowed'])
            system_prompt += tools_desc
        
        history = await agent.memory.get_history(f"session_{agent.id}", limit=5)
        context = ""
        for turn in history:
            context += f"{turn['role']}: {turn['content']}\n"
        
        full_prompt = f"{context}\nUsuario: {user_input}\nAsistente:"
        
        try:
            response = await self.llm_router.generate(full_prompt, system_prompt)
            return response
        except Exception as e:
            return f"Error generando respuesta: {e}"
    
    async def _handle_tool_calls(self, agent: Agent, response: str) -> str:
        pattern = re.compile(r'<tool_call>(\w+)\s+(.*?)</tool_call>', re.DOTALL)
        match = pattern.search(response)
        if not match:
            return response
        
        tool_name = match.group(1)
        args_str = match.group(2).strip()
        args = {}
        arg_pattern = re.compile(r'(\w+)=("[^"]*"|\'[^\']*\'|\S+)')
        for k, v in arg_pattern.findall(args_str):
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            elif v.startswith("'") and v.endswith("'"):
                v = v[1:-1]
            args[k] = v
        
        tool = agent.tools.get(tool_name)
        if tool and tool.enabled:
            try:
                result = await tool.execute(args, workspace=agent.workspace)
                return result
            except Exception as e:
                return f"Error ejecutando {tool_name}: {e}"
        else:
            tool_script = None
            for t in agent.config.get('tools', {}).get('native', []):
                if t['name'] == tool_name:
                    tool_script = t['script']
                    break
            if tool_script:
                agent_dir = Path(agent.config_path).parent
                full_script = agent_dir / tool_script
                if not full_script.exists():
                    return f"Error: Script no encontrado: {tool_script}"
                try:
                    result = subprocess.run(
                        ["python", str(full_script), json.dumps(args)],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        return result.stdout.strip()
                    else:
                        return f"Error ejecutando {tool_name}: {result.stderr}"
                except Exception as e:
                    return f"Error: {str(e)}"
            else:
                return f"Error: Herramienta '{tool_name}' no configurada"
