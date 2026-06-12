#!/usr/bin/env python3
import asyncio
import sys
from nanu.core.orchestrator import Orchestrator
from nanu.core.channels.cli import CLIChannel

async def main():
    print("🚀 NanuCore 3.0")
    
    orch = Orchestrator(agents_dir="agents", data_dir="nanu/data")
    await orch.load_agents()
    
    if not orch.agents:
        print("❌ No hay agentes")
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
    else:
        await cli.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Hasta luego")
