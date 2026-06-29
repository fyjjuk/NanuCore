"""Speech-to-Text service - Vosk + Faster-Whisper."""
import os
import sys
import json
import wave
from pathlib import Path
from typing import Optional

# Intentar importar faster-whisper
try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Faster-Whisper no instalado. Instalar: pip install faster-whisper")

# Vosk (fallback)
try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("⚠️ Vosk no instalado. Instalar: pip install vosk")

# Silenciar logs de Vosk
os.environ["VOSK_LOG_LEVEL"] = "-1"
os.environ["GLOG_minloglevel"] = "3"

# Constantes
MAX_FRAMES = 150000
MAX_FILE_SIZE = 20 * 1024 * 1024

class STTService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._model = None
        self._rec = None
        self._whisper_model = None
        self._use_whisper = WHISPER_AVAILABLE  # Priorizar Whisper si está disponible
    
    def _init_whisper(self):
        """Inicializa el modelo de Faster-Whisper."""
        if self._whisper_model is not None:
            return
        if not WHISPER_AVAILABLE:
            print("⚠️ Faster-Whisper no disponible, usando Vosk")
            self._use_whisper = False
            return
        
        try:
            print("📂 Cargando modelo Faster-Whisper (base)...")
            # Modelo "base" es rápido y preciso. "small" es más preciso pero más lento.
            self._whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            print("✅ Faster-Whisper listo")
        except Exception as e:
            print(f"⚠️ Error cargando Faster-Whisper: {e}")
            self._use_whisper = False
    
    def _init_vosk(self):
        """Inicializa el modelo de Vosk (fallback)."""
        if self._model is not None:
            return
        if not VOSK_AVAILABLE:
            self._model = False
            return
        
        try:
            # Buscar modelo
            model_path = Path("models/vosk/vosk-model-small-es-0.42")
            if not model_path.exists():
                model_path = Path.home() / ".cache/vosk/vosk-model-small-es-0.42"
            
            if not model_path.exists():
                print("⚠️ Modelo Vosk no encontrado. Usando solo Whisper.")
                self._model = False
                return
            
            print(f"📂 Cargando modelo Vosk desde: {model_path}")
            
            # Redirigir stderr
            stderr_fd = os.dup(2)
            devnull_fd = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull_fd, 2)
            
            self._model = Model(str(model_path))
            self._rec = KaldiRecognizer(self._model, 16000)
            
            os.dup2(stderr_fd, 2)
            os.close(stderr_fd)
            os.close(devnull_fd)
            
            print("✅ Vosk listo")
        except Exception as e:
            print(f"⚠️ Error cargando Vosk: {e}")
            self._model = False
    
    def transcribe(self, audio_path: str) -> str:
        """Transcribe usando Whisper (preferido) o Vosk (fallback)."""
        # Verificar archivo
        try:
            file_size = os.path.getsize(audio_path)
            if file_size > MAX_FILE_SIZE:
                print(f"⚠️ Archivo demasiado grande: {file_size} bytes")
                return ""
        except Exception as e:
            print(f"⚠️ Error verificando archivo: {e}")
            return ""
        
        # Si Whisper está disponible, usarlo primero
        if self._use_whisper:
            self._init_whisper()
            if self._whisper_model:
                try:
                    segments, info = self._whisper_model.transcribe(
                        audio_path,
                        language=None,  # Auto-detecta idioma (inglés/español)
                        task="transcribe",
                        beam_size=5,
                        vad_filter=True  # Filtra silencios
                    )
                    text = " ".join([seg.text for seg in segments])
                    if text:
                        return text.strip().lower()
                except Exception as e:
                    print(f"⚠️ Error en Whisper: {e}")
                    # Si falla Whisper, intentar con Vosk
        
        # Fallback a Vosk (solo español)
        self._init_vosk()
        if not self._model:
            return ""
        
        try:
            wf = wave.open(audio_path, 'rb')
        except Exception as e:
            print(f"⚠️ Error abriendo archivo: {e}")
            return ""
        
        parts = []
        frame_count = 0
        
        try:
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                frame_count += 1
                if frame_count > MAX_FRAMES:
                    break
                if self._rec.AcceptWaveform(data):
                    res = json.loads(self._rec.Result())
                    if res.get('text'):
                        parts.append(res['text'])
        except Exception as e:
            print(f"⚠️ Error en Vosk: {e}")
        
        try:
            final = json.loads(self._rec.FinalResult())
            if final.get('text'):
                parts.append(final['text'])
        except Exception:
            pass
        
        wf.close()
        return ' '.join(parts).strip().lower()
