"""
Cognitive Executor - Ejecución de rutas con stages y soporte de streaming
"""

import logging
from typing import Dict, Any

from .stage_executor import StageExecutor
from .streaming import StreamHandler

logger = logging.getLogger(__name__)


class LLMExecutor:
    """Ejecutor cognitivo para rutas con stages y streaming"""
    
    def __init__(self, agent):
        """Inicializa el ejecutor con el manifiesto del agente"""
        self.agent = agent
        self.stage_executor = StageExecutor(agent)
    
    def execute(self, agent, intent: Dict[str, Any], 
                query: str, router, rag_engine) -> str:
        """
        Ejecuta una ruta, ya sea con stages o simple
        
        Args:
            agent: Manifiesto del agente
            intent: Datos de la ruta a ejecutar
            query: Input sanitizado del usuario
            router: Router para determinar necesidades
            rag_engine: Motor RAG para contexto
            
        Returns:
            str: Respuesta generada
        """
        # Obtener core_config del engine si está disponible
        core_config = getattr(agent, 'core_config', {})
        if hasattr(agent, 'llm_client') and hasattr(agent.llm_client, 'core_config'):
            core_config = agent.llm_client.core_config
        
        # Verificar si la ruta tiene stages
        stages = intent.get("stages")
        if stages:
            logger.info(f"Ejecutando ruta con {len(stages)} stages")
            context = {}
            final_output = ""
            
            for stage in stages:
                stage_name = stage.get("name", "unknown")
                logger.debug(f"Ejecutando stage: {stage_name}")
                output, context = self.stage_executor.execute_stage(
                    stage, context, query, core_config
                )
                final_output = output  # la última etapa será la respuesta final
            
            # Si hay una clave de salida específica en la ruta, usarla
            final_key = intent.get("final_output_key", "respuesta_final")
            if final_key in context:
                return context[final_key]
            return final_output
        
        # Comportamiento original (sin stages)
        enhanced_prompt = query
        
        # Inyectar contexto RAG si es necesario
        if router.needs_rag_context(query, agent) and rag_engine:
            try:
                context_results = rag_engine.rag_query(agent.id, query, top_k=3)
                if context_results and context_results.get('documents'):
                    context_text = "\n\n".join(context_results['documents'][0])
                    enhanced_prompt = f"Contexto relevante:\n{context_text}\n\nConsulta: {query}"
                    logger.info(f"Contexto RAG inyectado ({len(context_text)} caracteres)")
            except Exception as e:
                logger.warning(f"Error consultando RAG: {e}")
        
        # Obtener LLM y configurar
        llm = agent.llm_client
        system_prompt = intent.get("system_prompt", "Eres un asistente útil.")
        llm_config = intent.get("model_config", {})
        
        # Inyectar timeout desde el agente si no está definido
        if "timeout" not in llm_config:
            llm_config["timeout"] = getattr(agent, "execution_timeout", 30)
        
        # Verificar si se debe usar streaming
        use_streaming = llm_config.get("stream", False)
        
        if use_streaming and hasattr(llm, 'stream_response'):
            logger.info("Usando streaming para la respuesta")
            response = ""
            for token in StreamHandler.stream_with_yield(llm, enhanced_prompt, system_prompt, llm_config):
                response += token
            return response
        else:
            # Streaming no disponible o desactivado, usar método normal
            output = llm.generate_response(enhanced_prompt, system_prompt, llm_config)
            output = self._parse_tool_call(output, agent, intent.get("tools_allowed", []))
            # Parsear tool calls
            return output
    
    def _stream_response(self, llm, prompt: str, system_prompt: str, llm_config: dict) -> str:
        """
        Método legacy para compatibilidad
        """
        return StreamHandler.stream_response_legacy(llm, prompt, system_prompt, llm_config)

    def _parse_tool_call(self, output: str, agent, tools_allowed: list) -> str:
        """Detecta y ejecuta tool calls en formato <tool_call>..."""
        import re
        import subprocess
        import json
        import os
        
        # Buscar patrón <tool_call>spotify_search query="valor"</tool_call> o query=valor
        patterns = [
            r'<tool_call>(\w+)\s+query="([^"]+)"\s*</tool_call>',
            r'<tool_call>(\w+)\s+query=([^\s>]+)\s*</tool_call>',
        ]
        match = None
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE | re.DOTALL)
            if match:
                break
        
        if match:
            tool_name = match.group(1)
            query = match.group(2).strip()
            
            logger.info(f"Tool call detectado: {tool_name} query='{query}'")
            
            # Verificar que la herramienta está permitida
            if tool_name in tools_allowed or f"native:{tool_name}" in tools_allowed:
                # Buscar la herramienta en el agente
                tool_script = None
                for tool in agent.tools.get("native", []):
                    if tool["name"] == tool_name:
                        tool_script = tool["script"]
                        break
                
                if tool_script:
                    # Construir ruta absoluta
                    agent_dir = os.path.join("agents", agent.id)
                    full_path = os.path.join(agent_dir, tool_script)
                    
                    if not os.path.exists(full_path):
                        full_path = os.path.join("tools", "native", os.path.basename(tool_script))
                    
                    if os.path.exists(full_path):
                        try:
                            args_str = json.dumps({"query": query})
                            result = subprocess.run(
                                ["python", full_path, args_str],
                                capture_output=True,
                                text=True,
                                timeout=10
                            )
                            if result.returncode == 0:
                                return result.stdout.strip()
                            else:
                                return f"Error: {result.stderr}"
                        except Exception as e:
                            return f"Error: {str(e)}"
                    else:
                        return f"Error: Herramienta no encontrada: {tool_script}"
                else:
                    return f"Error: Herramienta '{tool_name}' no configurada"
            else:
                return f"Error: Herramienta '{tool_name}' no permitida"
        
        return output
        import logging
        _logger = logging.getLogger("ferdonan.parser")
        
        _logger.info(f"PARSER: processing output: {output[:200]}")
        _logger.info(f"PARSER: tools_allowed: {tools_allowed}")
        _logger.info(f"PARSER: agent tools: {agent.tools.get('native', [])}")
