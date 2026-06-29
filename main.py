#!/usr/bin/env python3
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

# Cargar variables de entorno ANTES de configurar logging
load_dotenv('.env')

# Inicializar logging (usará LOG_LEVEL de las variables cargadas)
from nanu.core.logging import setup_logging
setup_logging()

from nanu.core.orchestrator import Orchestrator
from nanu.core.channels.cli import CLIChannel
from nanu.core.logging import get_logger

logger = get_logger(__name__)


def validate_agent_config(config_path: Path) -> tuple:
    """
    Valida un archivo de configuración de agente.
    Retorna (es_valido, mensaje_error)
    """
    if not config_path.exists():
        return False, f"Archivo no encontrado: {config_path}"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, f"Error YAML en {config_path.name}: {e}"
    except Exception as e:
        return False, f"Error leyendo {config_path.name}: {e}"
    
    # Validar campos requeridos
    required_fields = ['id', 'name']
    missing = [f for f in required_fields if f not in config]
    if missing:
        return False, f"Faltan campos requeridos en {config_path.name}: {', '.join(missing)}"
    
    # Validar que id no tenga caracteres especiales
    agent_id = config.get('id', '')
    if not agent_id or not agent_id.replace('_', '').replace('-', '').isalnum():
        return False, f"ID inválido en {config_path.name}: '{agent_id}' (solo letras, números, _ y -)"
    
    # Validar que el directorio de rutas existe
    routes_dir = config_path.parent / "routes"
    if not routes_dir.exists():
        logger.warning(f"Agente '{agent_id}': No hay directorio de rutas")
    
    # Validar configuración de LLM
    if 'llm' not in config:
        return False, f"Falta configuración 'llm' en {config_path.name}"
    
    llm_config = config.get('llm', {})
    if 'providers' not in llm_config or not llm_config['providers']:
        return False, f"Falta 'llm.providers' en {config_path.name}"
    
    return True, "OK"


async def main():
    print("🚀 NanuCore 3.0")
    
    # Validar agentes antes de cargarlos
    agents_dir = Path("agents")
    if agents_dir.exists():
        invalid_agents = []
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            config_path = agent_dir / "config.yaml"
            if not config_path.exists():
                continue
            
            is_valid, message = validate_agent_config(config_path)
            if not is_valid:
                invalid_agents.append((agent_dir.name, message))
                logger.warning(f"Agente inválido '{agent_dir.name}': {message}")
        
        if invalid_agents:
            print(f"\n⚠️ Se encontraron {len(invalid_agents)} agente(s) inválidos:")
            for name, msg in invalid_agents:
                print(f"   - {name}: {msg}")
            print("")
    
    # Cargar agentes
    orch = Orchestrator(agents_dir="agents", data_dir="nanu/data")
    try:
        await orch.load_agents()
    except Exception as e:
        logger.error(f"Error cargando agentes: {e}")
        print(f"❌ Error cargando agentes: {e}")
        return
    
    if not orch.agents:
        print("❌ No hay agentes disponibles")
        print("   Crea un agente en el directorio 'agents/' con un archivo config.yaml")
        return
    
    # Seleccionar agente
    agent = await orch.select_agent_interactive()
    if not agent:
        return
    
    print("\n" + "="*50)
    
    # Crear CLI con el agente seleccionado
    cli = CLIChannel(orch)
    cli.current_agent = agent
    
    # Verificar voz
    if agent.config.get('voice', {}).get('enabled', False):
        try:
            from nanu.core.channels.voice import VoiceChannel
            voice = VoiceChannel(agent)
            
            # Ejecutar ambos canales
            cli_task = asyncio.create_task(cli.run())
            voice_task = asyncio.create_task(voice.run())
            
            # Esperar a que CLI termine (por /exit)
            await cli_task
            
            # Detener voz
            voice.stop()
            await voice_task
        except ImportError as e:
            logger.warning(f"No se pudo cargar VoiceChannel: {e}")
            await cli.run()
        except Exception as e:
            logger.error(f"Error en VoiceChannel: {e}")
            await cli.run()
    else:
        await cli.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Hasta luego")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        print(f"\n❌ Error fatal: {e}")
        sys.exit(1)
