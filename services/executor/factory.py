from typing import Dict, Any
from .base import BaseExecutor
from .llm_executor import LLMExecutor
from .script_executor import ScriptExecutor

def create_executor(intent: Dict[str, Any], agent=None) -> BaseExecutor:
    route_type = intent.get("type", "cognitive")
    if route_type == "cognitive":
        if agent is None:
            raise ValueError("agent es requerido para LLMExecutor")
        return LLMExecutor(agent)
    elif route_type == "script":
        return ScriptExecutor()
    else:
        if agent is None:
            raise ValueError("agent es requerido para LLMExecutor")
        return LLMExecutor(agent)
