import time
import logging
from typing import List, Optional
import httpx
from app.providers.base import BaseAIProvider, ChatMessage, ProviderResponse
from app.config import settings

logger = logging.getLogger("alexa_ai.openai")

class OpenAIProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.provider_name = "openai"

    async def generate_response(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        timeout_seconds: Optional[float] = None
    ) -> ProviderResponse:
        timeout = timeout_seconds or settings.REQUEST_TIMEOUT_SECONDS
        prompt = system_prompt or settings.DEFAULT_SYSTEM_PROMPT
        
        # Build payload for OpenAI Chat Completions API
        api_messages = [{"role": "system", "content": prompt}]
        for m in messages:
            api_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": 0.7,
            "max_tokens": 250  # Keep voice responses concise
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException as exc:
                latency_ms = (time.perf_counter() - t0) * 1000.0
                logger.error(f"OpenAI API call timed out after {latency_ms:.1f}ms: {exc}")
                raise TimeoutError(f"OpenAI request timed out after {timeout}s") from exc
            except Exception as exc:
                latency_ms = (time.perf_counter() - t0) * 1000.0
                logger.error(f"OpenAI API call failed after {latency_ms:.1f}ms: {exc}")
                raise

        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0

        content = data["choices"][0]["message"]["content"] or ""
        return ProviderResponse(
            text=content.strip(),
            provider_name=self.provider_name,
            model_name=self.model,
            latency_ms=round(latency_ms, 2)
        )

