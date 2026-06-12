#!/usr/bin/env python3
"""Cliente WebSocket de ejemplo para NanuCore."""
import asyncio
import websockets
import json
import sys


async def main():
    uri = "ws://localhost:8765"

    try:
        async with websockets.connect(uri) as ws:
            print("✅ Conectado a NanuCore WebSocket\n")

            # Listar agentes
            await ws.send(json.dumps({"type": "list_agents"}))
            response = await ws.recv()
            data = json.loads(response)
            print("📋 Agentes disponibles:")
            for agent in data["agents"]:
                print(f"   - {agent['id']}: {agent['name']}")

            # Seleccionar agente (opcional)
            agent_id = sys.argv[1] if len(sys.argv) > 1 else None
            if agent_id:
                await ws.send(json.dumps({"type": "select_agent", "agent_id": agent_id}))
                response = await ws.recv()
                print(f"\n✅ {response}")

            # Bucle interactivo
            print("\n💬 Modo interactivo. Escribe 'exit' para salir.\n")
            while True:
                text = input("> ")
                if text.lower() in ("exit", "quit", "salir"):
                    break

                await ws.send(json.dumps({"type": "message", "text": text}))
                response = await ws.recv()
                data = json.loads(response)
                print(f"🤖 {data.get('text', data)}")

    except ConnectionRefusedError:
        print("❌ No se pudo conectar. ¿Está ejecutándose NanuCore?")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
