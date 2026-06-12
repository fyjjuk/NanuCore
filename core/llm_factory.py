from typing import Dict, Any
from core.logger import logger
from orchestration.resource_manager import ResourceScheduler

def create_llm_client(agent_id: str, manifest_data: dict, core_config: dict):
    from services.llm_providers import OllamaClient, GeminiClient, GroqClient, LocalClient
    
    provider = manifest_data.get("llm_provider", {}).get("name", "ollama")
    provider_config = manifest_data.get("llm_provider", {})
    
    if manifest_data.get("llm_provider", {}).get("dynamic_resource_management", False):
        scheduler = ResourceScheduler()
        profile = scheduler.select_resource_profile(manifest_data.get("llm_provider", {}))
        profile_config = manifest_data.get("llm_provider", {}).get("resource_profiles", {}).get(profile, {})
        if profile_config:
            provider_config.update(profile_config)
            logger.info(f"Perfil dinámico '{profile}' seleccionado para agente {agent_id}")
    
    if provider == "ollama":
        return OllamaClient(agent_id, provider_config, core_config)
    elif provider == "gemini":
        if not provider_config.get("api_key") and core_config.get("llm", {}).get("gemini", {}).get("api_key"):
            provider_config["api_key"] = core_config["llm"]["gemini"]["api_key"]
        return GeminiClient(agent_id, provider_config, core_config)
    elif provider == "groq":
        if not provider_config.get("api_key") and core_config.get("llm", {}).get("groq", {}).get("api_key"):
            provider_config["api_key"] = core_config["llm"]["groq"]["api_key"]
        return GroqClient(agent_id, provider_config, core_config)
    else:
        return LocalClient(agent_id, provider_config, core_config)
