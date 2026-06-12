import os
import sys
import yaml
from core.logger import logger
from config.settings import settings
import sys
sys.modules['tqdm'] = __import__('tqdm')
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
from models.agent_manifest import AgentManifest
from core.orchestrator import FerdoNANEngine
from persistence.memory_store import ShortTermMemory
from persistence.long_term_memory import LongTermMemory
from core.tracing import generate_request_id
from services.router.intent_router import RouteNotFoundError
from security.filters.ingress import IngressFilter
from core.llm_factory import create_llm_client
from core.i18n import t, Localization
from security.filters.egress import EgressFilter
from security.filters.semantic import SemanticOutputFilter
from ui.agent_selector import select_agent_interactive
from ui.cli_commands import process_slash_command

def check_ollama():
    import requests
    try:
        response = requests.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=3)
        if response.status_code == 200:
            print("\033[92m✅ Ollama está corriendo correctamente.\033[0m")
            return True
        else:
            print(f"\033[91m❌ Ollama responde con código {response.status_code}\033[0m")
            return False
    except requests.ConnectionError:
        print(f"\033[91m❌ No se pudo conectar a Ollama en {settings.OLLAMA_HOST}\033[0m")
        print("\033[93m   Asegúrate de ejecutar: ollama serve\033[0m")
        return False
    except Exception as e:
        print(f"\033[91m❌ Error verificando Ollama: {e}\033[0m")
        return False

def bootstrap_security_assets():
    from ui import ConsoleRenderer
    ui_renderer = ConsoleRenderer(theme_name=os.environ.get("FERDONAN_THEME", "refero"))
    from dotenv import load_dotenv
    load_dotenv()
    if not os.path.exists("config"):
        os.makedirs("config")
    security_files = {
        "config/ingress_blacklist.txt": "# Blacklist de comandos peligrosos (RegEx)\nrm -rf\nsudo\npasswd\n",
        "config/egress_cmd_blacklist.txt": "# Comandos prohibidos en salida\nrm\ncurl\nwget\n",
        "config/egress_tools_blacklist.txt": "# Herramientas prohibidas\ndangerous_tool\n"
    }
    for filepath, default_content in security_files.items():
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(default_content)
            logger.info(f"Archivo de seguridad creado: {filepath}")
    return True

def bootstrap_core():
    from dotenv import load_dotenv
    load_dotenv()
    bootstrap_security_assets()
    from ui import ConsoleRenderer
    ui_renderer = ConsoleRenderer(theme_name=os.environ.get("FERDONAN_THEME", "refero"))
    
    core_config = {}
    
    if not check_ollama():
        print("\033[93m⚠️  Ollama no está disponible. Los agentes que usen Ollama fallarán.\033[0m")
        print("\033[93mContinuando sin Ollama...\033[0m")

    ingress = IngressFilter(global_regex_path=settings.INGRESS_BLACKLIST_PATH, enabled_layer2=False)
    egress = EgressFilter(settings.EGRESS_CMD_BLACKLIST_PATH, settings.EGRESS_TOOLS_BLACKLIST_PATH)
    semantic = SemanticOutputFilter(default_enabled=False)
    
    from security.auth.gatekeeper import Gatekeeper
    
    gatekeeper = Gatekeeper(default_timeout=settings.GATEKEEPER_TIMEOUT, force_all=settings.GATEKEEPER_FORCE_ALL, ui_renderer=ui_renderer)
    cache = None
    engine = FerdoNANEngine(ingress=ingress, egress=egress, semantic=semantic,
                            gatekeeper=gatekeeper, cache=cache, ui_renderer=ui_renderer)
    engine.core_config = core_config
    
    from services.vector_store import RAGEngine
    engine.rag_engine = RAGEngine()
    
    agents_dir = "agents"
    loaded = {}
    
    if not os.path.exists(agents_dir):
        os.makedirs(agents_dir)
    
    for agent_id in os.listdir(agents_dir):
        path = os.path.join(agents_dir, agent_id)
        config_path = os.path.join(path, "config.yaml")
        if os.path.isdir(path) and os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                manifest = AgentManifest(**data)
                manifest.memory = ShortTermMemory(manifest.short_term_memory_window)
                manifest.long_term_memory = LongTermMemory(agent_id, engine.rag_engine)
                manifest.llm_client = create_llm_client(agent_id, data, core_config)

                routes_dir = os.path.join(path, "routes")
                routes_list = []
                if os.path.exists(routes_dir):
                    for route_file in os.listdir(routes_dir):
                        if route_file.endswith((".yaml", ".yml")):
                            with open(os.path.join(routes_dir, route_file), "r") as rf:
                                intent = yaml.safe_load(rf)
                                if intent and "route_id" in intent:
                                    routes_list.append(intent)
                manifest.routes_available = routes_list
                
                docs_dir = os.path.join(path, "docs")
                if os.path.exists(docs_dir) and engine.rag_engine:
                    for doc_file in os.listdir(docs_dir):
                        if doc_file.endswith(('.txt', '.md', '.docx', '.xlsx')):
                            file_path = os.path.join(docs_dir, doc_file)
                            try:
                                engine.rag_engine.process_and_index(agent_id, file_path)
                                logger.info(f"Documento indexado: {doc_file} para agente {agent_id}")
                            except Exception as e:
                                print(f"\033[93m⚠️ Error indexando {doc_file} para agente {agent_id}: {e}\033[0m")
                                logger.error(f"Error indexando {doc_file}: {e}")
                loaded[agent_id] = manifest
                logger.info(f"Agente {agent_id} cargado con éxito.", extra={"component": "core"})
                print(f"\033[92m✅ Agente {agent_id} cargado con éxito.\033[0m")
            except Exception as e:
                print(f"\033[91m❌ Error cargando agente {agent_id}: {e}\033[0m")
                logger.error(f"Error cargando agente {agent_id}: {e}", extra={"component": "core"})
    
    return engine, loaded

if __name__ == "__main__":
    engine, agents = bootstrap_core()
    generate_request_id()
    
    if not agents:
        print("❌ No se encontraron agentes configurados.")
        sys.exit(1)
    
    try:
        agent = select_agent_interactive(agents)
        if agent is None:
            print("👋 Selección cancelada. Saliendo...")
            sys.exit(0)
    except ImportError:
        print("⚠️ prompt_toolkit no instalado. Usando selector numérico.")
        from ui.agent_selector import select_agent
        agent = select_agent(agents)
        if agent is None:
            sys.exit(0)
    
    # --- Inicialización del asistente de voz (opcional) ---
    voice_assistant = None
    if os.environ.get("FERDONAN_VOICE_ENABLED", "true").lower() != "false":
        try:
            from services.voice.voice_assistant import init_voice_assistant
            voice_assistant = init_voice_assistant(engine, agents, agent, verbose=False)
        except Exception as e:
            print(f"[-] Error iniciando asistente de voz: {e}")
    
    print(f"[+] Agente Activo: {agent.name} ({agent.id})")
    print(f"[+] Concurrencia: {agent.execution_mode}")
    print(f"[+] Proveedor LLM: {agent.llm_provider.get('name', 'desconocido')}")
    print("[+] Escribe '/exit' para salir, '/help' para ayuda.\n")

    while True:
        try:
            user_input = input(f"\n[{agent.id}] > ").strip()
            if not user_input:
                continue

            if user_input.startswith('/'):
                msg, new_agent, should_exit = process_slash_command(user_input, agents, agent)
                print(msg)
                # Si cambiamos de agente, actualizar la referencia en el asistente de voz
                if voice_assistant and new_agent != agent:
                    agent = new_agent
                    voice_assistant.current_agent = agent
                    print(f"[+] Cambiado al agente: {agent.name}")
                    continue
                if should_exit:
                    break
                if new_agent != agent:
                    agent = new_agent
                    print(f"[+] Cambiado al agente: {agent.name}")
                continue

            if user_input.lower() in ('salir', 'exit', 'quit'):
                print("👋 ¡Hasta luego!")
                break

            output, summary = engine.process_pipeline(agent, user_input)
            print(f"\n[Enrutamiento Exitoso]")
            print(f" -> Ruta: {summary.get('route_id', 'unknown')}")
            print(f" -> Modo: {summary.get('execution_mode', 'exclusive')}")
            print(f" -> Respuesta:\n{output}")

        except PermissionError as pe:
            print(f"\n[!] BLOQUEADO POR FIREWALL: {pe}")
        except RouteNotFoundError as exc:
            print(f"\n[!] Ruta no encontrada: {exc}")
            if hasattr(exc, 'available_routes') and exc.available_routes:
                print("   Rutas disponibles:")
                for r in exc.available_routes:
                    print(f"     - {r.get('route_id')}: {r.get('description', '')[:50]}")
        except KeyboardInterrupt:
            print("\n[!] Interrupción recibida. Saliendo...")
            break
        except Exception as e:
            print(f"[-] Error: {e}")
            logger.error(f"Error en pipeline: {e}", extra={"component": "main"})
    
    # Al salir, detener el asistente de voz
    if voice_assistant:
        voice_assistant.stop()
        print("[Voz] Asistente de voz detenido.")
    sys.exit(0)
