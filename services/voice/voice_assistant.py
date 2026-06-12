import threading
import time
import tempfile
import os
import subprocess
import wave
import json
from vosk import KaldiRecognizer
from services.voice.stt import create_stt
from services.voice.tts import create_tts
from services.hotkey.evdev_listener import GlobalHotkeyListener
from core.logger import logger

class VoiceAssistant:
    def __init__(self, engine, agents, current_agent, verbose=False):
        self.engine = engine
        self.agents = agents
        self.current_agent = current_agent
        self.verbose = verbose
        self.is_recording = False
        self.audio_file = None
        
        self.stt = create_stt('vosk', 
                              model_path='models/vosk/vosk-model-small-es-0.42',
                              samplerate=48000,
                              device=None)
        self.tts = create_tts('edge', default_voice='es-ES-ElviraNeural', speed=180, pitch=65)
        
        self.hotkey_listener = GlobalHotkeyListener(
            self.start_recording,
            self.stop_recording,
            hotkey_mode="copilot_toggle"
        )
    
    def start(self):
        self.hotkey_listener.start()
        logger.info("VoiceAssistant iniciado")
        if self.verbose:
            print("[Voz] Asistente de voz activo. Presiona Copilot para hablar (modo toggle).")
    
    def stop(self):
        self.hotkey_listener.stop()
        subprocess.run(['pkill', '-f', 'espeak-ng'], stderr=subprocess.DEVNULL)
        logger.info("VoiceAssistant detenido")
        if self.verbose:
            print("[Voz] Asistente de voz detenido.")
    
    def start_recording(self):
        self.is_recording = True
        self.audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.audio_file.close()
        self.record_process = subprocess.Popen([
            'arecord', '-d', '0', '-r', '48000', '-c', '1',
            '-f', 'S16_LE', '-t', 'wav', self.audio_file.name
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("Grabación iniciada")
    
    def stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self.record_process.terminate()
        self.record_process.wait(timeout=2)
        print("[Voz] Transcribiendo...")
        text = self.transcribe_audio(self.audio_file.name)
        if text.strip():
            print(f"[Voz] Comando: {text}")
            self.process_command(text)
        else:
            print("[Voz] No se reconoció comando")
            self.tts.speak("No te entendí. Intenta de nuevo.", "es")
        try:
            os.unlink(self.audio_file.name)
        except:
            pass
    
    def transcribe_audio(self, audio_path):
        try:
            wf = wave.open(audio_path, 'rb')
            rec = KaldiRecognizer(self.stt.model, wf.getframerate())
            parts = []
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    if res.get('text'):
                        parts.append(res['text'])
            final = json.loads(rec.FinalResult())
            if final.get('text'):
                parts.append(final['text'])
            wf.close()
            return ' '.join(parts).strip()
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""
    
    def process_command(self, command_text):
        try:
            output, summary = self.engine.process_pipeline(self.current_agent, command_text)
            print("\n" + "="*50)
            print(f"[Agente {self.current_agent.name}]")
            print(f"Ruta: {summary.get('route_id', 'unknown')} | Modo: {summary.get('execution_mode', 'exclusive')}")
            print("-"*50)
            print(output)
            print("="*50 + "\n")
            if output and output != "ERROR_SEGURIDAD_EGRESS":
                threading.Thread(target=self.tts.speak, args=(output, None), daemon=True).start()
            else:
                threading.Thread(target=self.tts.speak, args=("No pude procesar tu solicitud", None), daemon=True).start()
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            threading.Thread(target=self.tts.speak, args=("Error interno", None), daemon=True).start()

def init_voice_assistant(engine, agents, current_agent, verbose=False):
    assistant = VoiceAssistant(engine, agents, current_agent, verbose=verbose)
    assistant.start()
    return assistant
