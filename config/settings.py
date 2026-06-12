from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os

class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- Configuración General ---
    PROJECT_NAME: str = "FerdoNAN"
    VERSION: str = "2.3.0"
    LOG_LEVEL: str = "INFO"
    OLLAMA_HOST: str = "http://localhost:11434"

    # --- API Keys ---
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # --- Seguridad ---
    INGRESS_BLACKLIST_PATH: str = "config/ingress_blacklist.txt"
    EGRESS_CMD_BLACKLIST_PATH: str = "config/egress_cmd_blacklist.txt"
    EGRESS_TOOLS_BLACKLIST_PATH: str = "config/egress_tools_blacklist.txt"
    GATEKEEPER_TIMEOUT: int = 60
    GATEKEEPER_FORCE_ALL: bool = False
    RATE_LIMIT_MAX_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # --- Pipeline ---
    DEFAULT_EXECUTION_TIMEOUT: int = 30

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

# Instancia global de la configuración para importar en otros módulos
settings = CoreSettings()
