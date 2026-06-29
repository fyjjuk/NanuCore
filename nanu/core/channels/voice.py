"""Canal de voz con hotkey Copilot y silenciamiento de TTS al grabar."""
import asyncio
import tempfile
import subprocess
import threading
import shutil
import os
from pathlib import Path
from typing import Optional

from nanu.core.audio import STTService, TTSService
from nanu.core.pipeline import Pipeline
from nanu.core.logging import get_logger

logger = get_logger(__name__)

# Verificar dependencias
def _check_dependencies() -> tuple:
    """Verifica que las dependencias necesarias estén instaladas."""
    errors = []
    
    # Verificar evdev
    try:
        import evdev
    except ImportError:
        errors.append("evdev no instalado (pip install evdev)")
    
    # Verificar arecord (ALSA)
    if not shutil.which('arecord'):
        errors.append("arecord no encontrado (instalar alsa-utils)")
    
    # Verificar mpg123 (para TTS)
    if not shutil.which('mpg123'):
        errors.append("mpg123 no encontrado (instalar mpg123)")
    
    # Verificar edge-tts (para TTS en la nube)
    try:
        import edge_tts
    except ImportError:
        errors.append("edge-tts no instalado (pip install edge-tts)")
    
    return len(errors) == 0, errors


class VoiceChannel:
    def __init__(self, agent):
        self.agent = agent
        self.stt = STTService()
        self.tts = TTSService()
        self.pipeline = Pipeline()
        self._recording = False
        self._running = True
        self._stop_event = threading.Event()
        self._hotkey_thread = None
        self._keyboard = None
        self._available = False
        self._dependencies_ok = False
        self._dependencies_errors = []
    
    def _check_availability(self) -> bool:
        """Verifica disponibilidad del canal de voz."""
        if not self.agent.config.get('voice', {}).get('enabled', False):
            logger.info("Canal de voz desactivado en configuración")
            return False
        
        ok, errors = _check_dependencies()
        if not ok:
            self._dependencies_errors = errors
            for err in errors:
                logger.warning(f"Voz: {err}")
            return False
        
        self._dependencies_ok = True
        return True
    
    async def run(self):
        """Inicia el canal de voz."""
        if not self._check_availability():
            print("🎤 Canal de voz no disponible. Verifica dependencias.")
            return
        
        print(f"🎤 Voz activada para: {self.agent.name}")
        print("🎤 Presiona Copilot (F23) para hablar")
        print("🎤 Presiona Ctrl+C para salir del modo voz")
        
        self._available = True
        self._stop_event.clear()
        
        # Iniciar listener en hilo separado
        self._hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self._hotkey_thread.start()
        
        while self._running and not self._stop_event.is_set():
            await asyncio.sleep(0.5)
    
    def stop(self):
        """Detiene el canal de voz."""
        self._running = False
        self._stop_event.set()
        
        # Detener grabación en curso
        if self._recording:
            self._stop_recording()
        
        # Detener TTS
        self.tts.stop()
        
        if self._hotkey_thread and self._hotkey_thread.is_alive():
            self._hotkey_thread.join(timeout=2)
        
        logger.info("Canal de voz detenido")
    
    def _hotkey_listener(self):
        """Escucha la tecla Copilot en un hilo separado."""
        try:
            import evdev
            from evdev import ecodes
            
            # Buscar teclado
            devices = [evdev.InputDevice(p) for p in evdev.list_devices()]
            keyboard = None
            for dev in devices:
                if 'keyboard' in dev.name.lower():
                    keyboard = dev
                    break
            
            if not keyboard:
                logger.warning("No se encontró teclado para hotkey de voz")
                print("🎤 No se encontró teclado")
                return
            
            self._keyboard = keyboard
            logger.info(f"Teclado detectado: {keyboard.name}")
            print(f"🎤 Teclado: {keyboard.name}")
            
            for event in keyboard.read_loop():
                if self._stop_event.is_set():
                    break
                if event.type == ecodes.EV_KEY:
                    key = evdev.categorize(event)
                    if key.keycode in ('KEY_F23', 'KEY_COPILOT') and key.keystate == key.key_down:
                        if not self._recording:
                            self._start_recording()
                        else:
                            self._stop_recording()
        except Exception as e:
            if not self._stop_event.is_set():
                logger.error(f"Error en listener de teclado: {e}")
                print(f"🎤 Error en hotkey: {e}")
    
    def _start_recording(self):
        """Inicia la grabación de audio."""
        if not self._available:
            return
        
        # Detener TTS en curso
        self.tts.stop()
        
        self._recording = True
        self._audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self._audio_file.close()
        
        try:
            self._record_process = subprocess.Popen([
                'arecord', '-d', '0', '-r', '16000', '-c', '1',
                '-f', 'S16_LE', '-t', 'wav', self._audio_file.name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("\n🎤 Grabando... (presiona Copilot para detener)")
        except Exception as e:
            logger.error(f"Error iniciando grabación: {e}")
            self._recording = False
            if hasattr(self, '_audio_file') and self._audio_file:
                try:
                    os.unlink(self._audio_file.name)
                except:
                    pass
    
    def _stop_recording(self):
        """Detiene la grabación y procesa el audio."""
        if not self._recording:
            return
        
        self._recording = False
        
        # Detener proceso de grabación
        if hasattr(self, '_record_process') and self._record_process:
            try:
                self._record_process.terminate()
                self._record_process.wait(timeout=2)
            except Exception as e:
                logger.error(f"Error deteniendo grabación: {e}")
        
        print("🎤 Procesando...")
        
        # Transcribir
        try:
            text = self.stt.transcribe(self._audio_file.name)
        except Exception as e:
            logger.error(f"Error transcribiendo: {e}")
            text = ""
        
        if text:
            print(f"🎤 Dijiste: {text}")
            
            # Procesar en event loop separado para no bloquear
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response, _ = loop.run_until_complete(
                    self.pipeline.run(self.agent, text, "voice")
                )
                loop.close()
                
                print(f"\n[Respuesta] {response}")
                print(f"\n[{self.agent.id}] > ", end="", flush=True)
                self.tts.speak(response, async_mode=True)
            except Exception as e:
                logger.error(f"Error procesando respuesta: {e}")
                print(f"\n[Error] {e}")
        else:
            print("\n🎤 No entendí")
            print(f"\n[{self.agent.id}] > ", end="", flush=True)
        
        # Limpiar archivo temporal
        try:
            if self._audio_file and os.path.exists(self._audio_file.name):
                os.unlink(self._audio_file.name)
        except Exception:
            pass
    
    def is_available(self) -> bool:
        """Retorna True si el canal de voz está disponible."""
        return self._available
    
    def get_dependency_errors(self) -> list:
        """Retorna la lista de errores de dependencias."""
        return self._dependencies_errors
