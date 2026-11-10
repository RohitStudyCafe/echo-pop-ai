from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Literal

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ProviderResponse(BaseModel):
    text: str
    provider_name: str
    model_name: str
    latency_ms: float

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_response(
        self, 
        messages: list[ChatMessage], 
        system_prompt: str,
        timeout_seconds: float
    ) -> ProviderResponse:
        pass

