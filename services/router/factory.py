from services.router.keyword import KeywordRouter
from services.router.ollama import OllamaRouter

def create_router(config: dict):
    mode = config.get("mode", "keyword")
    threshold = config.get("threshold", 0.3)
    model = config.get("model")
    
    if mode == "keyword":
        return KeywordRouter(threshold=threshold)
    elif mode == "ollama" and model:
        return OllamaRouter(model=model, threshold=threshold)
    else:
        return KeywordRouter(threshold=threshold)
