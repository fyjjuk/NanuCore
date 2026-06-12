from services.voice.stt.vosk_stt import VoskSTT

def create_stt(provider: str = "vosk", **kwargs):
    """Fábrica para crear instancias STT."""
    if provider == "vosk":
        model_path = kwargs.get("model_path", "models/vosk/vosk-model-small-es-0.42")
        samplerate = kwargs.get("samplerate", 48000)
        device = kwargs.get("device", None)
        return VoskSTT(model_path, samplerate, device)
    else:
        raise ValueError(f"Proveedor STT no soportado: {provider}")
