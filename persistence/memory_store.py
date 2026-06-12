from collections import deque
import json
import os
import hashlib
from core.logger import logger

class ShortTermMemory:
    def __init__(self, window_size: int = 5, agent_id: str = None):
        self.window_size = window_size
        self.window = deque(maxlen=window_size)
        self.agent_id = agent_id
        self._load_from_disk() if agent_id else None

    def _get_memory_file(self):
        return f"data/memory_{self.agent_id}_short.json"

    def _load_from_disk(self):
        path = self._get_memory_file()
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.window = deque(data.get('messages', []), maxlen=self.window_size)
                    logger.info(f"Memoria corto plazo cargada para {self.agent_id}: {len(self.window)} mensajes")
            except Exception as e:
                logger.warning(f"Error cargando memoria: {e}")

    def _save_to_disk(self):
        if not self.agent_id:
            return
        os.makedirs("data", exist_ok=True)
        path = self._get_memory_file()
        with open(path, 'w') as f:
            json.dump({'messages': list(self.window)}, f)

    def add(self, message: str):
        if len(self.window) >= self.window_size:
            logger.info(f"MEMORY_SHORT_TERM_EVICT: Evicting oldest message for {self.agent_id}")
        self.window.append(message)
        self._save_to_disk()

    def get_context(self):
        return list(self.window)

    def clear(self):
        self.window.clear()
        self._save_to_disk()
