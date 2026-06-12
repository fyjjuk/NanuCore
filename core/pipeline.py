from typing import Tuple, Dict, Any
from core.logger import logger
from core.factory import create_router, create_sanitizer
from services.router.intent_router import RouteNotFoundError
from config.settings import settings
from persistence.cache import should_cache

def run_pipeline(agent, raw_input: str, 
                 ingress, egress, semantic, 
                 gatekeeper, cache, rag_engine,
                 core_config: dict) -> Tuple[str, Dict[str, Any]]:
    """
    Ejecuta el pipeline completo de procesamiento:
    1. Sanitiza el input
    2. Valida con firewall Ingress
    3. Enruta la consulta
    4. Opcionalmente verifica con Gatekeeper
    5. Ejecuta la ruta (con caché)
    6. Valida con firewall Egress
    7. Filtra salida semántica
    """
    router = create_router(agent)
    sanitizer = create_sanitizer(agent)

    query = sanitizer.clean(raw_input)
    if not ingress.evaluate(query, agent):
        raise PermissionError("Entrada bloqueada por Firewall Ingress.")

    from orchestration.resource_manager import ResourceScheduler
    scheduler = ResourceScheduler()
    
    can_parallel, reason = scheduler.can_run_parallel(agent)
    effective_mode = "parallel" if can_parallel else scheduler.suggest_degradation(agent.id)
    logger.info(f"PIPELINE_START: agent_id={agent.id}, mode={effective_mode}")

    try:
        route_id, confidence, intent = router.route(agent.id, query)
    except RouteNotFoundError as e:
        logger.warning(f"Router: {str(e)}")
        raise

    gatekeeper_required = intent.get("gatekeeper_required", False)
    force_gatekeeper = core_config.get("pipeline", {}).get("gatekeeper", {}).get("force_for_all_routes", settings.GATEKEEPER_FORCE_ALL)
    
    if gatekeeper_required or force_gatekeeper:
        from security.auth.gatekeeper import Gatekeeper
        from core.tracing import get_request_id
        timeout = core_config.get("pipeline", {}).get("gatekeeper", {}).get("default_timeout_seconds", settings.GATEKEEPER_TIMEOUT)
        gk = gatekeeper if gatekeeper is not None else Gatekeeper(default_timeout=timeout, force_all=force_gatekeeper)
        request_id = get_request_id() or "unknown"
        if not gk.verify(route_id, intent, request_id):
            raise PermissionError(f"Acción rechazada por Gatekeeper. Ruta: {route_id}")

    # --- Lógica de caché mejorada ---
    cache_enabled = cache is not None and hasattr(agent, 'cache_config') and agent.cache_config.enabled
    
    if cache_enabled and should_cache(intent, cache_enabled):
        cached_output = cache.get(route_id, query)
        if cached_output:
            output = cached_output
        else:
            from services.executor.factory import create_executor
            executor = create_executor(intent, agent)
            output = executor.execute(agent, intent, query, router, rag_engine)
            cache.set(route_id, query, output)
    else:
        from services.executor.factory import create_executor
        executor = create_executor(intent, agent)
        output = executor.execute(agent, intent, query, router, rag_engine)

    if not egress.evaluate(output, intent):
        return "ERROR_SEGURIDAD_EGRESS", {"status": "blocked", "route_id": route_id}
    output = semantic.evaluate_and_replace(output, intent)

    return output, {
        "route_id": route_id,
        "confidence": confidence,
        "execution_mode": effective_mode
    }
