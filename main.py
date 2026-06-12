#!/usr/bin/env python3
"""Punto de entrada para NanuCore 3.0 con canales CLI y WebSocket."""
import asyncio
from nanu.core.orchestrator import Orchestrator
from nanu.core.channels.cli import CLIChannel
from nanu.core.channels.websocket import WebSocketChannel
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("🚀 Iniciando NanuCore 3.0...")
    
    orchestrator = Orchestrator(agents_dir="agents", data_dir="nanu/data")
    await orchestrator.load_agents()
    
    if not orchestrator.agents:
        print("❌ No se encontraron agentes.")
        return
    
    # Iniciar WebSocket
    ws_channel = WebSocketChannel(orchestrator, host="localhost", port=8765)
    ws_task = asyncio.create_task(ws_channel.start())
    await asyncio.sleep(0.5)
    
    # Iniciar CLI
    cli_channel = CLIChannel(orchestrator)
    try:
        await cli_channel.run()
    except KeyboardInterrupt:
        print("\n👋 Interrupción recibida.")
    finally:
        print("🛑 Deteniendo WebSocket...")
        await ws_channel.stop()
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass
        print("👋 Hasta luego!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Saliendo...")
