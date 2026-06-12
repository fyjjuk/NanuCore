import os
os.environ["VOSK_LOG_LEVEL"] = "-1"

import json
import queue
import sys
import contextlib
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from services.voice.interfaces import BaseSTT

class VoskSTT(BaseSTT):
    def __init__(self, model_path: str, samplerate: int = 48000, device: int = None):
        # Redirigir stderr a null temporalmente mientras se carga el modelo
        self._original_stderr_fd = None
        self._devnull_fd = None
        try:
            # Guardar el descriptor original de stderr
            self._original_stderr_fd = os.dup(2)
            self._devnull_fd = os.open(os.devnull, os.O_WRONLY)
            os.dup2(self._devnull_fd, 2)  # Redirigir stderr (fd 2) a /dev/null
            # Cargar el modelo (los logs se irán a null)
            self.model = Model(model_path)
        finally:
            # Restaurar stderr original
            if self._original_stderr_fd is not None:
                os.dup2(self._original_stderr_fd, 2)
                os.close(self._original_stderr_fd)
            if self._devnull_fd is not None:
                os.close(self._devnull_fd)

        self.samplerate = samplerate
        self.device = device
        self.rec = KaldiRecognizer(self.model, samplerate)

    def transcribe(self, duration: float = 3.0) -> str:
        q = queue.Queue()
        def callback(indata, frames, time, status):
            if status:
                print(f"Error de audio: {status}")
            q.put(bytes(indata))

        device = self.device if self.device is not None else None
        print(f"🎤 Escuchando... (dispositivo {device}, {self.samplerate} Hz)")
        with sd.RawInputStream(samplerate=self.samplerate, blocksize=8000, device=device,
                               dtype='int16', channels=1, callback=callback):
            for _ in range(int(self.samplerate * duration / 8000)):
                data = q.get()
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    text = result.get('text', '')
                    if text:
                        return text
        final = json.loads(self.rec.FinalResult())
        text = final.get('text', '')
        return text

    def transcribe_bytes(self, audio_bytes: bytes) -> str:
        if self.rec.AcceptWaveform(audio_bytes):
            result = json.loads(self.rec.Result())
            return result.get('text', '')
        return ''
