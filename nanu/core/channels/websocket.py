"""Canal WebSocket para NanuCore."""
import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from nanu.core.orchestrator import Orchestrator
from nanu.core.pipeline import Pipeline

class WebSocketChannel:
    def __init__(self, orchestrator: Orchestrator, host: str = "localhost", port: int = 8765):
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.sessions: Dict[str, Dict] = {}
        self.server = None
        self._stop_event = asyncio.Event()
    
    async def handler(self, websocket):
        session_id = str(uuid.uuid4())
        current_agent_id = None
        pipeline = Pipeline(event_bus=self.orchestrator.event_bus)
        
        print(f"[WS] Nueva conexión: {session_id}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "message")
                    
                    if msg_type == "message":
                        user_input = data.get("text", "")
                        if not user_input:
                            continue
                        
                        if not current_agent_id and self.orchestrator.agents:
                            current_agent_id = list(self.orchestrator.agents.keys())[0]
                        
                        agent = self.orchestrator.get_agent(current_agent_id) if current_agent_id else None
                        if not agent:
                            await websocket.send(json.dumps({"error": "No hay agente seleccionado"}))
                            continue
                        
                        response, metadata = await pipeline.run(agent, user_input, f"ws_{session_id}")
                        await websocket.send(json.dumps({
                            "type": "response",
                            "text": response,
                            "metadata": metadata
                        }))
                    
                    elif msg_type == "select_agent":
                        agent_id = data.get("agent_id")
                        if agent_id in self.orchestrator.agents:
                            current_agent_id = agent_id
                            await websocket.send(json.dumps({
                                "type": "agent_selected",
                                "agent_id": agent_id,
                                "agent_name": self.orchestrator.agents[agent_id].name
                            }))
                        else:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "error": f"Agente '{agent_id}' no encontrado"
                            }))
                    
                    elif msg_type == "list_agents":
                        agents = self.orchestrator.list_agents()
                        await websocket.send(json.dumps({
                            "type": "agent_list",
                            "agents": agents
                        }))
                    
                    else:
                        await websocket.send(json.dumps({"error": f"Tipo de mensaje desconocido: {msg_type}"}))
                
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"error": "Mensaje debe ser JSON válido"}))
                except Exception as e:
                    await websocket.send(json.dumps({"error": str(e)}))
        
        except Exception as e:
            print(f"[WS] Error en conexión {session_id}: {e}")
        finally:
            print(f"[WS] Conexión cerrada: {session_id}")
    
    async def start(self):
        import websockets
        self.server = await websockets.serve(self.handler, self.host, self.port)
        print(f"[WS] Servidor WebSocket iniciado en ws://{self.host}:{self.port}")
        await self._stop_event.wait()  # Esperar hasta que se solicite detener
        self.server.close()
        await self.server.wait_closed()
        print("[WS] Servidor WebSocket detenido")
    
    async def stop(self):
        self._stop_event.set()
