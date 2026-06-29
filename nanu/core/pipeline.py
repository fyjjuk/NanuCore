from pathlib import Path
import asyncio
import subprocess
import json
import re
import shlex
from typing import Dict, Any, Tuple, Optional
from nanu.core.agent import Agent
from nanu.core.routing.intent_router import IntentRouter
from nanu.core.routing.model_router import ModelRouter
from nanu.core.events.bus import EventBus
from nanu.core.events.hooks import HookManager
from nanu.core.cache import DiskCache
from nanu.core.providers import create_llm_router
from nanu.core.audio.corrections import corrector
from nanu.core.logging import get_logger

logger = get_logger(__name__)

# Constantes de seguridad
MAX_INPUT_LENGTH = 4096
BLOCKED_PATTERNS = [
    r'rm\s+-rf\s+[/]?',           # rm -rf /
    r'sudo\s+',                   # sudo
    r'passwd\s+',                 # passwd
    r'chmod\s+777\s+[/]?',        # chmod 777 /
    r'>\s*/dev/sd[a-z]',          # Redirección a disco
    r'mkfs\.',                    # mkfs (formatear)
    r'dd\s+if=',                  # dd (disco)
    r'wget\s+.*\|.*sh',           # wget | sh
    r'curl\s+.*\|.*sh',           # curl | sh
    r'python\s+-c\s+',            # python -c (ejecutar código)
    r'eval\s*\(',                 # eval()
    r'exec\s*\(',                 # exec()
    r'system\s*\(',               # system()
    r'`.*`',                      # backticks (subshell)
    r'\$\(.*\)',                  # $(comando)
]

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
    
    def _sanitize_input(self, text: str) -> str:
        """
        Sanitiza el input del usuario:
        - Elimina caracteres de control (excepto \n)
        - Limita la longitud
        - Normaliza espacios
        - Elimina caracteres no imprimibles
        """
        if not text:
            return ""
        
        import unicodedata
        sanitized = []
        for char in text:
            cat = unicodedata.category(char)
            if (cat.startswith('L') or  # Letras
                cat.startswith('N') or  # Números
                cat.startswith('P') or  # Puntuación
                cat.startswith('S') or  # Símbolos
                cat.startswith('Z') or  # Espacios
                cat == 'Cc' and char in '\n\t'):  # Control permitido
                sanitized.append(char)
            elif cat == 'Cc':
                continue
            else:
                sanitized.append(char)
        
        text = ''.join(sanitized)
        
        if len(text) > MAX_INPUT_LENGTH:
            text = text[:MAX_INPUT_LENGTH]
            logger.warning(f"Input truncado a {MAX_INPUT_LENGTH} caracteres")
        
        text = re.sub(r'[ \t]+', ' ', text)
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _is_blocked(self, text: str) -> bool:
        """Verifica si el input contiene patrones peligrosos."""
        text_lower = text.lower()
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.debug(f"Bloqueo por patrón: {pattern}")
                return True
        return False
    
    def _is_egress_blocked(self, text: str) -> bool:
        """Verifica si la respuesta contiene comandos peligrosos."""
        dangerous = ["rm", "curl", "wget", "sudo", "chmod", "chown", "passwd"]
        for cmd in dangerous:
            if f" {cmd} " in f" {text} " or text.startswith(f"{cmd} "):
                logger.debug(f"Egress bloqueado por comando: {cmd}")
                return True
        return False
    
    async def run(self, agent: Agent, user_input: str, session_key: str) -> Tuple[str, Dict[str, Any]]:
        context = {"agent": agent, "session_key": session_key}
        
        # 1. Corrección fonética (STT)
        corrected_input = corrector.correct(user_input)
        if corrected_input != user_input:
            logger.info(f"Corrección fonética: '{user_input}' → '{corrected_input}'")
        
        # 2. Sanitización del input
        sanitized_input = self._sanitize_input(corrected_input)
        if not sanitized_input:
            return "No se detectó entrada válida.", {"route_id": "none", "model": "none"}
        
        # 3. Pre-hooks (después de sanitizar)
        processed_input = await self.hook_manager.run_pre_hooks(sanitized_input, context)
        if not processed_input.strip():
            return "No se detectó entrada.", {"route_id": "none", "model": "none"}
        
        # 4. Bloqueo de seguridad
        if self._is_blocked(processed_input):
            logger.warning(f"Entrada bloqueada por seguridad: '{processed_input[:100]}'")
            return "Entrada bloqueada por políticas de seguridad.", {"route_id": "blocked"}
        
        await self.event_bus.publish("pipeline.sanitized", {"input": processed_input})
        
        # 5. Pre-route hooks
        routed_input = await self.hook_manager.run_pre_route_hooks(processed_input, context)
        
        # 6. Enrutamiento
        route = self.intent_router.route(agent, routed_input)
        if not route:
            logger.debug(f"No se pudo determinar la intención para: '{routed_input}'")
            return "No se pudo determinar la intención.", {"route_id": "unknown"}
        
        route_id = await self.hook_manager.run_post_route_hooks(route['route_id'], routed_input, context)
        if route_id != route['route_id']:
            route = agent.get_route(route_id) or route
            logger.debug(f"Ruta modificada por hook: {route_id}")
        
        await self.event_bus.publish("pipeline.routed", {"route_id": route['route_id']})
        
        # 7. Gatekeeper
        if hasattr(agent, 'gatekeeper') and agent.gatekeeper:
            approved = await agent.gatekeeper.verify(route['route_id'], route, session_key, session_key)
            if not approved:
                logger.info(f"Acción rechazada por Gatekeeper: {route['route_id']}")
                return "Acción rechazada por Gatekeeper.", {"route_id": route['route_id'], "blocked": True}
        
        # 8. Ejecución
        route_type = route.get('type', 'cognitive')
        try:
            if route_type == 'script':
                response = await self._execute_script(agent, route, sanitized_input)
            else:
                cache_enabled = hasattr(agent, 'cache_config') and agent.cache_config.enabled
                cached = None
                if cache_enabled:
                    system_prompt = route.get('system_prompt', "")
                    cached = self.cache.get(agent.id, route['route_id'], sanitized_input, system_prompt)
                if cached:
                    response = cached
                    logger.debug(f"Cache hit para {agent.id}/{route['route_id']}")
                    await self.event_bus.publish("pipeline.cache_hit", {"route_id": route['route_id']})
                else:
                    response = await self._execute_cognitive(agent, route, sanitized_input)
                    if cache_enabled:
                        ttl = getattr(agent.cache_config, 'ttl', 3600)
                        system_prompt = route.get('system_prompt', "")
                        self.cache.set(agent.id, route['route_id'], sanitized_input, response, system_prompt, ttl)
                response = await self._handle_tool_calls(agent, response)
            
            # 9. Egress filter
            if self._is_egress_blocked(response):
                logger.warning(f"Respuesta bloqueada por egress filter: {response[:100]}...")
                response = "La respuesta fue bloqueada por políticas de seguridad."
            
            # 10. Post-hooks
            response = await self.hook_manager.run_post_hooks(response, context)
            
        except Exception as e:
            logger.error(f"Error en pipeline: {e}", exc_info=True)
            await self.hook_manager.run_error_hooks(e, sanitized_input, context)
            return f"Error en pipeline: {e}", {"route_id": route['route_id'], "error": str(e)}
        
        # 11. Memoria
        await agent.memory.add(session_key, {"role": "user", "content": sanitized_input, "timestamp": None})
        await agent.memory.add(session_key, {"role": "assistant", "content": response, "timestamp": None})
        
        metadata = {"route_id": route['route_id'], "execution_mode": agent.execution_mode}
        await self.event_bus.publish("pipeline.completed", {"response": response, "metadata": metadata})
        return response, metadata
    
    async def _execute_script(self, agent: Agent, route: Dict, user_input: str) -> str:
        script_path = route.get('script_path')
        if not script_path:
            return "Error: script_path no definido"
        agent_dir = Path(agent.config_path).parent
        full_script = agent_dir / script_path
        if not full_script.exists():
            logger.warning(f"Script no encontrado: {full_script}")
            return f"Error: herramienta no encontrada: {script_path}"
        args = route.get('script_args', {})
        processed = {}
        for k, v in args.items():
            if isinstance(v, str) and "{user_input}" in v:
                processed[k] = v.replace("{user_input}", user_input)
            else:
                processed[k] = v
        try:
            logger.debug(f"Ejecutando script: {full_script} con args: {processed}")
            process = subprocess.Popen(
                ["python", str(full_script), json.dumps(processed)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            try:
                stdout, stderr = process.communicate(timeout=30)
                if process.returncode == 0:
                    return stdout.strip()
                else:
                    logger.warning(f"Script falló: {stderr}")
                    return f"Error: {stderr}"
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
                return "Error: El script excedió el tiempo límite de 30 segundos"
        except Exception as e:
            logger.error(f"Error ejecutando script: {e}")
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
            logger.debug(f"LLM request para {agent.id}: {full_prompt[:200]}...")
            response = await self.llm_router.generate(full_prompt, system_prompt)
            return response
        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return f"Error generando respuesta: {e}"
    
    async def _handle_tool_calls(self, agent: Agent, response: str) -> str:
        """
        Procesa tool calls en la respuesta del LLM.
        Soporta formato: <tool_call>nombre args</tool_call>
        Donde args puede ser:
        - key=value (simple)
        - key="valor con espacios"
        - key='valor con comillas'
        - key={"json": "object"} (JSON)
        """
        pattern = re.compile(r'<tool_call>(\w+)\s+(.*?)</tool_call>', re.DOTALL)
        match = pattern.search(response)
        if not match:
            return response
        
        tool_name = match.group(1)
        args_str = match.group(2).strip()
        args = {}
        
        # Intentar parsear como JSON primero
        if args_str.startswith('{') and args_str.endswith('}'):
            try:
                args = json.loads(args_str)
                logger.debug(f"Tool call parseado como JSON: {tool_name} -> {args}")
            except json.JSONDecodeError:
                pass
        
        # Si no es JSON o falló, parsear manualmente
        if not args:
            try:
                parts = shlex.split(args_str)
                for part in parts:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        # Intentar parsear valores numéricos
                        if value.isdigit():
                            value = int(value)
                        elif value.replace('.', '').isdigit():
                            value = float(value)
                        elif value.lower() in ('true', 'false'):
                            value = value.lower() == 'true'
                        elif value.lower() == 'null':
                            value = None
                        args[key] = value
                    else:
                        if 'arg' not in args:
                            args['arg'] = part
                        else:
                            i = 1
                            while f'arg{i}' in args:
                                i += 1
                            args[f'arg{i}'] = part
            except ValueError as e:
                logger.warning(f"Error parseando tool call con shlex: {e}")
                arg_pattern = re.compile(r'(\w+)=("[^"]*"|\'[^\']*\'|[^\s]+)')
                for k, v in arg_pattern.findall(args_str):
                    if v.startswith('"') and v.endswith('"'):
                        v = v[1:-1]
                    elif v.startswith("'") and v.endswith("'"):
                        v = v[1:-1]
                    if v.isdigit():
                        v = int(v)
                    elif v.replace('.', '').isdigit():
                        v = float(v)
                    args[k] = v
        
        logger.debug(f"Tool call detectado: {tool_name} con args: {args}")
        
        # Buscar herramienta nativa (Tool class)
        tool = agent.tools.get(tool_name)
        if tool and tool.enabled:
            try:
                result = await tool.execute(args, workspace=agent.workspace)
                return result
            except Exception as e:
                logger.error(f"Error ejecutando tool {tool_name}: {e}")
                return f"Error ejecutando {tool_name}: {e}"
        
        # Buscar script nativo
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
            except subprocess.TimeoutExpired:
                return f"Error: El script {tool_name} excedió el tiempo límite"
            except Exception as e:
                return f"Error: {str(e)}"
        else:
            return f"Error: Herramienta '{tool_name}' no configurada"
