import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from services.voice.interfaces import BaseSTT

class VoskSTT(BaseSTT):
    def __init__(self, model_path: str, samplerate: int = 48000, device: int = 8):
        self.model = Model(model_path)
        self.samplerate = samplerate
        self.device = device
        self.rec = KaldiRecognizer(self.model, samplerate)

    def transcribe(self, duration: float = 3.0) -> str:
        """Graba durante `duration` segundos y transcribe."""
        q = queue.Queue()
        def callback(indata, frames, time, status):
            if status:
                print(f"Error de audio: {status}")
            q.put(bytes(indata))
        
        print(f"🎤 Escuchando... (dispositivo {self.device}, {self.samplerate} Hz)")
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=self.device,
                               dtype='int16', channels=1, callback=callback):
            for _ in range(int(self.samplerate * duration / 8000)):
                data = q.get()
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get('text', '')
                    if text:
                        return text
        # Si no se reconoció nada, devolver lo último parcial
        final = json.loads(self.rec.FinalResult())
        text = final.get('text', '')
        return text

    def transcribe_bytes(self, audio_bytes: bytes) -> str:
        """Transcribe audio en bytes (útil para pruebas)."""
        if self.rec.AcceptWaveform(audio_bytes):
            result = json.loads(self.rec.Result())
            return result.get('text', '')
        return ''
