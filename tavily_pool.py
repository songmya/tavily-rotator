import threading
import time
from tavily import TavilyClient

class TavilyPool:
    def __init__(self, api_keys, cooldown=60):
        self.keys = api_keys
        self.index = 0
        self.cooldown = cooldown
        self.lock = threading.Lock()

        self.key_status = {
            key: {"last_failed": 0}
            for key in api_keys
        }

    def _get_next_key(self):
        with self.lock:
            for _ in range(len(self.keys)):
                key = self.keys[self.index]
                self.index = (self.index + 1) % len(self.keys)

                if time.time() - self.key_status[key]["last_failed"] > self.cooldown:
                    return key

            raise Exception("All API keys in cooldown")

    def search(self, query, **kwargs):
        for _ in range(len(self.keys)):
            key = self._get_next_key()

            try:
                client = TavilyClient(api_key=key)
                return client.search(query=query, **kwargs)
            except Exception:
                print(f"Key failed: {key}")
                self.key_status[key]["last_failed"] = time.time()
                continue

        raise Exception("All Tavily keys failed")