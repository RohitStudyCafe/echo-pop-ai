import logging
from typing import List, Optional, Dict, Any
from app.config import settings
from app.providers.base import ChatMessage

logger = logging.getLogger("alexa_ai.storage")

class BaseStorageRepository:
    async def save_turn(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        provider: Optional[str] = None,
        latency_ms: Optional[float] = None
    ) -> None:
        raise NotImplementedError

    async def get_history(self, user_id: str, limit: int = 10) -> List[ChatMessage]:
        raise NotImplementedError

    async def clear_history(self, user_id: str) -> None:
        raise NotImplementedError

class NullStorageRepository(BaseStorageRepository):
    """
    Default safe repository used when PERSISTENCE_ENABLED=False.
    Does not attempt any live database connections.
    """
    async def save_turn(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        provider: Optional[str] = None,
        latency_ms: Optional[float] = None
    ) -> None:
        pass

    async def get_history(self, user_id: str, limit: int = 10) -> List[ChatMessage]:
        return []

    async def clear_history(self, user_id: str) -> None:
        pass

class InMemoryStorageRepository(BaseStorageRepository):
    """
    In-memory fallback repository for local testing.
    """
    def __init__(self):
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    async def save_turn(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        provider: Optional[str] = None,
        latency_ms: Optional[float] = None
    ) -> None:
        if user_id not in self._store:
            self._store[user_id] = []
        self._store[user_id].append({
            "session_id": session_id,
            "role": role,
            "content": content,
            "provider": provider,
            "latency_ms": latency_ms
        })

    async def get_history(self, user_id: str, limit: int = 10) -> List[ChatMessage]:
        history = self._store.get(user_id, [])
        recent = history[-limit:]
        return [ChatMessage(role=item["role"], content=item["content"]) for item in recent]

    async def clear_history(self, user_id: str) -> None:
        if user_id in self._store:
            self._store[user_id] = []

def get_storage_repository() -> BaseStorageRepository:
    """
    Factory returning NullStorageRepository if PERSISTENCE_ENABLED is False,
    preventing any automatic database calls.
    """
    if not settings.PERSISTENCE_ENABLED:
        return NullStorageRepository()
    
    # When enabled by the user with a configured database URL
    # Live database connection can be established here manually by user
    logger.info("Database persistence enabled in settings.")
    return InMemoryStorageRepository()

