"""Sistema de logging centralizado para NanuCore."""
import logging
import os
import sys
from typing import Optional

# Configuración por defecto
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logging_initialized = False

def setup_logging(level: Optional[str] = None, log_file: Optional[str] = None) -> None:
    """
    Configura el sistema de logging para toda la aplicación.
    
    Args:
        level: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL). 
               Si no se proporciona, se lee de la variable de entorno LOG_LEVEL.
        log_file: Ruta opcional a un archivo de log.
    """
    global _logging_initialized
    
    if _logging_initialized:
        return
    
    # Determinar nivel
    if level is None:
        level = os.environ.get("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    level = level.upper()
    
    # Validar nivel
    numeric_level = getattr(logging, level, None)
    if not isinstance(numeric_level, int):
        print(f"[WARN] Nivel de log inválido: {level}. Usando {DEFAULT_LOG_LEVEL}.")
        level = DEFAULT_LOG_LEVEL
        numeric_level = getattr(logging, level)
    
    # Configurar handlers
    handlers = []
    
    # Handler para consola (siempre presente)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT))
    handlers.append(console_handler)
    
    # Handler para archivo (opcional)
    if log_file:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT))
            handlers.append(file_handler)
        except Exception as e:
            print(f"[WARN] No se pudo crear archivo de log {log_file}: {e}")
    
    # Configurar el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Eliminar handlers existentes para evitar duplicados
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Añadir nuevos handlers
    for handler in handlers:
        root_logger.addHandler(handler)
    
    _logging_initialized = True
    
    # Log inicial
    logging.info(f"Logging configurado: nivel={level}, archivo={log_file or 'solo consola'}")


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger para un módulo específico.
    Si el logging no está inicializado, lo inicializa con valores por defecto.
    """
    if not _logging_initialized:
        setup_logging()
    return logging.getLogger(name)


def set_level(level: str) -> None:
    """Cambia el nivel de log en tiempo de ejecución."""
    numeric_level = getattr(logging, level.upper(), None)
    if isinstance(numeric_level, int):
        logging.getLogger().setLevel(numeric_level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(numeric_level)
        logging.info(f"Nivel de log cambiado a: {level.upper()}")
    else:
        logging.warning(f"Nivel de log inválido: {level}")


__all__ = ['setup_logging', 'get_logger', 'set_level']
