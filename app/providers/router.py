import logging
from typing import List, Optional, Dict
from app.config import settings
from app.providers.base import BaseAIProvider, ChatMessage, ProviderResponse
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.utils.latency import LatencyTracker

logger = logging.getLogger("alexa_ai.router")

class ProviderRouter:
    def __init__(
        self,
        openai_provider: Optional[BaseAIProvider] = None,
        gemini_provider: Optional[BaseAIProvider] = None
    ):
        self.providers: Dict[str, BaseAIProvider] = {
            "openai": openai_provider or OpenAIProvider(),
            "gemini": gemini_provider or GeminiProvider()
        }

    def get_provider(self, name: str) -> Optional[BaseAIProvider]:
        norm = name.strip().lower()
        if "chatgpt" in norm or "gpt" in norm or "openai" in norm:
            return self.providers.get("openai")
        if "gemini" in norm or "google" in norm:
            return self.providers.get("gemini")
        return self.providers.get(norm)

    async def generate_with_fallback(
        self,
        messages: List[ChatMessage],
        requested_provider: Optional[str] = None,
        system_prompt: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        tracker: Optional[LatencyTracker] = None
    ) -> ProviderResponse:
        primary_name = (requested_provider or settings.DEFAULT_PROVIDER).lower()
        fallback_name = "gemini" if primary_name == "openai" else "openai"

        primary = self.get_provider(primary_name)
        fallback = self.get_provider(fallback_name)

        if not primary:
            logger.warning(f"Unknown provider '{primary_name}', defaulting to openai.")
            primary = self.providers["openai"]
            primary_name = "openai"

        # Attempt primary provider
        try:
            if tracker:
                tracker.mark_ai_start(provider=primary_name, model=getattr(primary, "model", "default"))
            
            resp = await primary.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                timeout_seconds=timeout_seconds
            )
            if tracker:
                tracker.mark_ai_end()
            return resp
        except Exception as exc:
            logger.warning(
                f"Primary AI provider '{primary_name}' failed: {exc}. Attempting fallback to '{fallback_name}'."
            )
            if tracker:
                tracker.mark_fallback()

        # Attempt fallback provider
        if fallback:
            try:
                if tracker:
                    tracker.mark_ai_start(provider=fallback_name, model=getattr(fallback, "model", "default"))
                
                resp = await fallback.generate_response(
                    messages=messages,
                    system_prompt=system_prompt,
                    timeout_seconds=timeout_seconds
                )
                if tracker:
                    tracker.mark_ai_end()
                return resp
            except Exception as fb_exc:
                logger.error(f"Fallback AI provider '{fallback_name}' also failed: {fb_exc}")

        raise RuntimeError("All configured AI providers failed to generate a response.")

