import time
import logging
from typing import List, Optional
import httpx
from app.providers.base import BaseAIProvider, ChatMessage, ProviderResponse
from app.config import settings

logger = logging.getLogger("alexa_ai.gemini")

class GeminiProvider(BaseAIProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.provider_name = "gemini"

    async def generate_response(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        timeout_seconds: Optional[float] = None
    ) -> ProviderResponse:
        timeout = timeout_seconds or settings.REQUEST_TIMEOUT_SECONDS
        prompt = system_prompt or settings.DEFAULT_SYSTEM_PROMPT

        # Map ChatMessage roles to Gemini roles ('user' and 'model')
        contents = []
        for m in messages:
            gemini_role = "model" if m.role == "assistant" else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": m.content}]
            })

        payload = {
            "system_instruction": {
                "parts": [{"text": prompt}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 250
            }
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
            except httpx.TimeoutException as exc:
                latency_ms = (time.perf_counter() - t0) * 1000.0
                logger.error(f"Gemini API call timed out after {latency_ms:.1f}ms: {exc}")
                raise TimeoutError(f"Gemini request timed out after {timeout}s") from exc
            except Exception as exc:
                latency_ms = (time.perf_counter() - t0) * 1000.0
                logger.error(f"Gemini API call failed after {latency_ms:.1f}ms: {exc}")
                raise

        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0

        try:
            candidates = data.get("candidates", [])
            parts = candidates[0]["content"]["parts"]
            content = parts[0]["text"]
        except (IndexError, KeyError) as e:
            logger.error(f"Failed to parse Gemini response structure: {data}")
            raise ValueError("Unexpected response structure from Gemini API") from e

        return ProviderResponse(
            text=content.strip(),
            provider_name=self.provider_name,
            model_name=self.model,
            latency_ms=round(latency_ms, 2)
        )

