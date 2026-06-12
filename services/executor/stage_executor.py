"""
Stage Runner - Lógica de ejecución de stages multi-LLM
"""

import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class StageExecutor:
    """Responsable de ejecutar stages individuales y validar sus salidas"""
    
    def __init__(self, agent):
        self.agent = agent
    
    def execute_stage(self, stage_config: Dict, context: Dict, 
                      query: str, core_config: Dict) -> Tuple[str, Dict]:
        """Ejecuta un stage individual (LLM o tool)"""
        stage_type = stage_config.get("type", "llm")
        stage_name = stage_config.get("name", "unknown")
        output_key = stage_config.get("output_key", "output")
        
        if stage_type == "llm":
            return self._execute_llm_stage(stage_config, context, query, core_config, stage_name, output_key)
        elif stage_type == "tool":
            return self._execute_tool_stage(stage_config, output_key)
        else:
            context[output_key] = query
            return query, context
    
    def _execute_llm_stage(self, stage_config: Dict, context: Dict, 
                           query: str, core_config: Dict,
                           stage_name: str, output_key: str) -> Tuple[str, Dict]:
        """Ejecuta un stage de tipo LLM"""
        prompt_template = stage_config.get("prompt", "{{input}}")
        formatted_prompt = prompt_template
        if "{{input}}" in prompt_template:
            formatted_prompt = prompt_template.replace("{{input}}", query)
        if "{{context}}" in prompt_template:
            formatted_prompt = formatted_prompt.replace("{{context}}", str(context))
        
        system_prompt = stage_config.get("system_prompt", "Eres un asistente útil.")
        llm_config = stage_config.get("model_config", {})
        provider_name = stage_config.get("provider", "ollama")
        llm = self.agent.llm_client
        
        logger.info(f"Ejecutando stage '{stage_name}' con proveedor: {provider_name}")
        
        try:
            output = llm.generate_response(formatted_prompt, system_prompt, llm_config)
            
            if self.validate_stage_output(output, stage_name, output_key):
                context[output_key] = output
            else:
                logger.warning(f"Stage '{stage_name}' output inválido. Reintentando.")
                output = llm.generate_response(formatted_prompt, system_prompt, llm_config)
                if self.validate_stage_output(output, stage_name, output_key):
                    context[output_key] = output
                else:
                    context[output_key] = f"[ERROR: Salida inválida del stage]"
                    return f"Error: Salida inválida", context
            
            return output, context
        except Exception as e:
            logger.error(f"Error en stage '{stage_name}': {e}")
            context[output_key] = f"[ERROR: {str(e)}]"
            return f"Error: {str(e)}", context
    
    def _execute_tool_stage(self, stage_config: Dict, output_key: str) -> Tuple[str, Dict]:
        """Ejecuta un stage de tipo tool (placeholder para futura implementación)"""
        tool_name = stage_config.get("tool", "")
        tool_params = stage_config.get("params", {})
        result = f"Tool {tool_name} executed with params {tool_params}"
        context = {output_key: result}
        return result, context
    
    def validate_stage_output(self, output: str, stage_name: str, output_key: str) -> bool:
        """Valida que la salida del stage sea válida"""
        if output is None:
            logger.error(f"Stage '{stage_name}' output es None")
            return False
        if not isinstance(output, str):
            logger.error(f"Stage '{stage_name}' output no es string: {type(output)}")
            return False
        if len(output.strip()) == 0:
            logger.error(f"Stage '{stage_name}' output está vacío")
            return False
        if len(output) > 10000:
            logger.warning(f"Stage '{stage_name}' output muy largo: {len(output)} chars")
        return True
