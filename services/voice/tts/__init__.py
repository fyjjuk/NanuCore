def create_tts(provider: str = "edge", **kwargs):
    if provider == "edge":
        from services.voice.tts.edge_tts import EdgeTTS
        default_voice = kwargs.get("default_voice", "es-ES-ElviraNeural")
        return EdgeTTS(default_voice)
    else:
        # Fallback a espeak-ng (local)
        from services.voice.tts.espeak_tts import EspeakTTS
        return EspeakTTS(
            default_voice=kwargs.get("default_voice", "es"),
            speed=kwargs.get("speed", 180),
            pitch=kwargs.get("pitch", 65)
        )
