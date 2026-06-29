"""Speech-to-Text service - Vosk."""
import os
import sys
import json
import wave
from pathlib import Path

# Silenciar Vosk completamente
os.environ["VOSK_LOG_LEVEL"] = "-1"
os.environ["GLOG_minloglevel"] = "3"

# Redirigir stderr durante importación
_stderr_fd = os.dup(2)
_devnull_fd = os.open(os.devnull, os.O_WRONLY)
os.dup2(_devnull_fd, 2)

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("⚠️ Vosk no instalado. Instalar: pip install vosk")

os.dup2(_stderr_fd, 2)
os.close(_stderr_fd)
os.close(_devnull_fd)

# Constantes de seguridad
MAX_FRAMES = 150000       # ~37.5 segundos a 16kHz (4000 frames * 150000 / 16000 = 37.5s)
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

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
    
    def _init_model(self):
        if self._model is not None:
            return
        if not VOSK_AVAILABLE:
            self._model = False
            return
        
        try:
            model_path = Path("models/vosk/vosk-model-small-es-0.42")
            if not model_path.exists():
                self._download_model()
            
            # Redirigir stderr durante carga
            stderr_fd = os.dup(2)
            devnull_fd = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull_fd, 2)
            
            self._model = Model(str(model_path))
            self._rec = KaldiRecognizer(self._model, 16000)
            
            os.dup2(stderr_fd, 2)
            os.close(stderr_fd)
            os.close(devnull_fd)
            
            print("✅ STT listo")
        except Exception as e:
            print(f"⚠️ Error STT: {e}")
            self._model = False
    
    def _download_model(self):
        import urllib.request
        import zipfile
        print("📥 Descargando modelo Vosk...")
        Path("models/vosk").mkdir(parents=True, exist_ok=True)
        url = "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"
        zip_path = Path("models/vosk/model.zip")
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall("models/vosk")
        zip_path.unlink()
        print("✅ Modelo listo")
    
    def transcribe(self, audio_path: str) -> str:
        """
        Transcribe un archivo de audio con límites de seguridad:
        - Límite de frames (evita DoS por archivos muy largos)
        - Límite de tamaño de archivo (20 MB)
        """
        self._init_model()
        if not self._model:
            return ""
        
        # Verificar tamaño del archivo
        try:
            file_size = os.path.getsize(audio_path)
            if file_size > MAX_FILE_SIZE:
                print(f"⚠️ Archivo demasiado grande: {file_size} bytes (límite: {MAX_FILE_SIZE})")
                return ""
        except Exception as e:
            print(f"⚠️ Error verificando tamaño de archivo: {e}")
            return ""
        
        try:
            wf = wave.open(audio_path, 'rb')
        except Exception as e:
            print(f"⚠️ Error abriendo archivo de audio: {e}")
            return ""
        
        parts = []
        frame_count = 0
        
        try:
            while True:
                data = wf.readframes(4000)
                if not data:
                    break
                
                # Límite de seguridad: máximo de frames
                frame_count += 1
                if frame_count > MAX_FRAMES:
                    print(f"⚠️ Límite de frames excedido ({MAX_FRAMES}), truncando...")
                    break
                
                if self._rec.AcceptWaveform(data):
                    res = json.loads(self._rec.Result())
                    if res.get('text'):
                        parts.append(res['text'])
        except Exception as e:
            print(f"⚠️ Error durante transcripción: {e}")
        
        try:
            final = json.loads(self._rec.FinalResult())
            if final.get('text'):
                parts.append(final['text'])
        except Exception as e:
            print(f"⚠️ Error obteniendo resultado final: {e}")
        
        wf.close()
        return ' '.join(parts).strip().lower()
