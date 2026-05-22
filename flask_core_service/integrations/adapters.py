from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

import requests


class ThirdPartyApiAdapter(ABC):
    @abstractmethod
    def fetch(self) -> Dict[str, Any]:
        raise NotImplementedError


class JsonPlaceholderAdapter(ThirdPartyApiAdapter):
    """Adapter para consumir una API de terceros y normalizar su salida."""

    def __init__(self, url: str = "https://jsonplaceholder.typicode.com/todos/1") -> None:
        self.url = url

    def fetch(self) -> Dict[str, Any]:
        response = requests.get(self.url, timeout=10)
        response.raise_for_status()
        payload = response.json()

        return {
            "provider": "jsonplaceholder",
            "source_url": self.url,
            "fetched_at": datetime.utcnow().isoformat(),
            "data": {
                "id": payload.get("id"),
                "title": payload.get("title"),
                "completed": payload.get("completed"),
                "user_id": payload.get("userId"),
            },
        }
