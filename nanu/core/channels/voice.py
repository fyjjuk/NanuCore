"""Canal de voz con hotkey Copilot y silenciamiento de TTS al grabar."""
import asyncio
import tempfile
import subprocess
import threading
import evdev
from evdev import ecodes
from nanu.core.audio import STTService, TTSService
from nanu.core.pipeline import Pipeline

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
    
    async def run(self):
        print(f"🎤 Voz activada para: {self.agent.name}")
        print("🎤 Presiona Copilot (F23) para hablar")
        
        self._stop_event.clear()
        self._hotkey_thread = threading.Thread(target=self._hotkey_listener, daemon=True)
        self._hotkey_thread.start()
        
        while self._running and not self._stop_event.is_set():
            await asyncio.sleep(0.5)
    
    def stop(self):
        self._running = False
        self._stop_event.set()
        if self._hotkey_thread and self._hotkey_thread.is_alive():
            self._hotkey_thread.join(timeout=2)
    
    def _hotkey_listener(self):
        try:
            for dev in [evdev.InputDevice(p) for p in evdev.list_devices()]:
                if 'keyboard' in dev.name.lower():
                    self._keyboard = dev
                    break
            else:
                print("🎤 No se encontró teclado")
                return
            
            print(f"🎤 Teclado: {self._keyboard.name}")
            
            for event in self._keyboard.read_loop():
                if self._stop_event.is_set():
                    break
                if event.type == ecodes.EV_KEY:
                    key = evdev.categorize(event)
                    # Soporta tanto KEY_F23 como KEY_COPILOT
                    if key.keycode in ('KEY_F23', 'KEY_COPILOT') and key.keystate == key.key_down:
                        if not self._recording:
                            self._start_recording()
                        else:
                            self._stop_recording()
        except Exception as e:
            if not self._stop_event.is_set():
                print(f"🎤 Hotkey error: {e}")
    
    def _start_recording(self):
        # Detener cualquier TTS en curso antes de empezar a grabar
        self.tts.stop()
        
        self._recording = True
        self._audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self._audio_file.close()
        self._record_process = subprocess.Popen([
            'arecord', '-d', '0', '-r', '16000', '-c', '1',
            '-f', 'S16_LE', '-t', 'wav', self._audio_file.name
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("\n🎤 Grabando... (presiona Copilot para detener)")
    
    def _stop_recording(self):
        if not self._recording:
            return
        self._recording = False
        if hasattr(self, '_record_process') and self._record_process:
            self._record_process.terminate()
            self._record_process.wait(timeout=2)
        print("🎤 Procesando...")
        
        text = self.stt.transcribe(self._audio_file.name)
        
        if text:
            print(f"🎤 Dijiste: {text}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response, _ = loop.run_until_complete(
                self.pipeline.run(self.agent, text, "voice")
            )
            loop.close()
            
            print(f"\n[Respuesta] {response}")
            print(f"\n[{self.agent.id}] > ", end="", flush=True)
            self.tts.speak(response, async_mode=True)
        else:
            print("\n🎤 No entendí")
            print(f"\n[{self.agent.id}] > ", end="", flush=True)
        
        try:
            import os
            os.unlink(self._audio_file.name)
        except:
            pass
