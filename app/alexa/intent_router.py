import logging
from typing import Dict, Any, Optional
from app.alexa.models import AlexaRequestEnvelope, AlexaResponseEnvelope
from app.alexa.response_builder import build_ask_response, build_tell_response, build_error_response
from app.memory.session_context import (
    get_history_from_session,
    append_to_session_history,
    clear_session_history,
    get_preferred_provider,
    set_preferred_provider
)
from app.memory.storage import get_storage_repository
from app.providers.router import ProviderRouter
from app.providers.base import ChatMessage
from app.utils.text_cleaner import clean_text_for_alexa
from app.utils.latency import LatencyTracker
from app.config import settings

logger = logging.getLogger("alexa_ai.intent_router")

class AlexaIntentRouter:
    def __init__(self, provider_router: Optional[ProviderRouter] = None):
        self.provider_router = provider_router or ProviderRouter()
        self.storage = get_storage_repository()

    async def handle_request(
        self,
        envelope: AlexaRequestEnvelope,
        tracker: Optional[LatencyTracker] = None
    ) -> AlexaResponseEnvelope:
        req = envelope.request
        session = envelope.session
        session_attrs = session.attributes if session else {}
        user_id = session.user.userId if (session and session.user) else "anonymous_user"
        session_id = session.sessionId if session else "unknown_session"

        req_type = req.type
        logger.info(f"Incoming Alexa request type='{req_type}', requestId='{req.requestId}'")

        if req_type == "LaunchRequest":
            return self._handle_launch(session_attrs)
        elif req_type == "IntentRequest":
            return await self._handle_intent(
                req.intent,
                session_attrs,
                user_id=user_id,
                session_id=session_id,
                tracker=tracker
            )
        elif req_type == "SessionEndedRequest":
            logger.info(f"Alexa session ended. Reason: {req.reason}")
            return build_tell_response("Goodbye", session_attributes=session_attrs)
        else:
            logger.warning(f"Unhandled Alexa request type: {req_type}")
            return build_tell_response("I didn't recognize that request type.")

    def _handle_launch(self, session_attrs: Dict[str, Any]) -> AlexaResponseEnvelope:
        welcome_text = "Hi, I'm your cloud AI assistant. What would you like to know?"
        reprompt_text = "You can ask me a question, or say switch to Gemini."
        return build_ask_response(
            text=welcome_text,
            reprompt_text=reprompt_text,
            session_attributes=session_attrs
        )

    async def _handle_intent(
        self,
        intent_data: Optional[Any],
        session_attrs: Dict[str, Any],
        user_id: str,
        session_id: str,
        tracker: Optional[LatencyTracker] = None
    ) -> AlexaResponseEnvelope:
        if not intent_data:
            return build_ask_response("I'm not sure what you meant. What would you like to ask?")

        intent_name = intent_data.name if hasattr(intent_data, "name") else intent_data.get("name")
        slots = intent_data.slots if hasattr(intent_data, "slots") else intent_data.get("slots", {})

        logger.info(f"Handling intent: {intent_name}")

        if intent_name == "AskAIIntent":
            return await self._handle_ask_ai(slots, session_attrs, user_id, session_id, tracker)
        elif intent_name == "SwitchProviderIntent":
            return self._handle_switch_provider(slots, session_attrs)
        elif intent_name == "ClearMemoryIntent":
            return await self._handle_clear_memory(session_attrs, user_id)
        elif intent_name == "GetStatusIntent":
            return self._handle_get_status(session_attrs)
        elif intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
            return build_tell_response("Goodbye!")
        elif intent_name == "AMAZON.HelpIntent":
            help_text = (
                "You can ask me any question, say switch to Gemini or switch to OpenAI, "
                "or say clear memory. What would you like to ask?"
            )
            return build_ask_response(text=help_text, reprompt_text="What would you like to ask?", session_attributes=session_attrs)
        elif intent_name == "AMAZON.FallbackIntent":
            fallback_text = "I didn't quite catch that. What would you like to ask?"
            return build_ask_response(text=fallback_text, reprompt_text="You can ask me anything.", session_attributes=session_attrs)
        else:
            return build_ask_response(f"I received {intent_name}, but I'm not sure how to handle it yet. What's on your mind?")

    async def _handle_ask_ai(
        self,
        slots: Optional[Dict[str, Any]],
        session_attrs: Dict[str, Any],
        user_id: str,
        session_id: str,
        tracker: Optional[LatencyTracker] = None
    ) -> AlexaResponseEnvelope:
        # Extract query slot
        query_text = ""
        if slots:
            slot_info = slots.get("Query") or slots.get("query")
            if isinstance(slot_info, dict):
                query_text = slot_info.get("value", "")
            elif hasattr(slot_info, "value"):
                query_text = slot_info.value or ""

        if not query_text or not query_text.strip():
            return build_ask_response(
                text="What would you like me to look up or explain?",
                reprompt_text="Please tell me what you'd like to ask.",
                session_attributes=session_attrs
            )

        # Retrieve conversation history from session attributes
        history = get_history_from_session(session_attrs)
        history.append(ChatMessage(role="user", content=query_text))

        # Check preferred provider
        active_provider = get_preferred_provider(session_attrs) or settings.DEFAULT_PROVIDER

        try:
            ai_resp = await self.provider_router.generate_with_fallback(
                messages=history,
                requested_provider=active_provider,
                tracker=tracker
            )
            spoken_text = clean_text_for_alexa(ai_resp.text)
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return build_ask_response(
                text="I'm having trouble connecting to the AI service right now. Please try again in a moment.",
                reprompt_text="What would you like to ask?",
                session_attributes=session_attrs
            )

        # Update sliding-window session history
        updated_attrs = append_to_session_history(session_attrs, role="user", content=query_text)
        updated_attrs = append_to_session_history(updated_attrs, role="assistant", content=spoken_text)

        # Save to persistent storage if enabled (safe no-op if disabled)
        await self.storage.save_turn(
            user_id=user_id,
            session_id=session_id,
            role="user",
            content=query_text,
            provider=ai_resp.provider_name
        )
        await self.storage.save_turn(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=spoken_text,
            provider=ai_resp.provider_name,
            latency_ms=ai_resp.latency_ms
        )

        return build_ask_response(
            text=spoken_text,
            reprompt_text="Is there anything else you'd like to ask?",
            session_attributes=updated_attrs
        )

    def _handle_switch_provider(
        self,
        slots: Optional[Dict[str, Any]],
        session_attrs: Dict[str, Any]
    ) -> AlexaResponseEnvelope:
        provider_val = ""
        if slots:
            slot_info = slots.get("Provider") or slots.get("provider")
            if isinstance(slot_info, dict):
                provider_val = slot_info.get("value", "")
            elif hasattr(slot_info, "value"):
                provider_val = slot_info.value or ""

        target = provider_val.strip().lower()
        if "gemini" in target or "google" in target:
            selected = "gemini"
            friendly_name = "Google Gemini"
        elif "chatgpt" in target or "openai" in target or "gpt" in target:
            selected = "openai"
            friendly_name = "OpenAI"
        else:
            selected = "openai"
            friendly_name = "OpenAI"

        updated_attrs = set_preferred_provider(session_attrs, selected)
        return build_ask_response(
            text=f"Switched provider to {friendly_name}. What would you like to ask?",
            reprompt_text="What would you like to ask?",
            session_attributes=updated_attrs
        )

    async def _handle_clear_memory(
        self,
        session_attrs: Dict[str, Any],
        user_id: str
    ) -> AlexaResponseEnvelope:
        updated_attrs = clear_session_history(session_attrs)
        await self.storage.clear_history(user_id)
        return build_ask_response(
            text="I've cleared our conversation memory. What would you like to talk about next?",
            reprompt_text="What's on your mind?",
            session_attributes=updated_attrs
        )

    def _handle_get_status(self, session_attrs: Dict[str, Any]) -> AlexaResponseEnvelope:
        active = get_preferred_provider(session_attrs) or settings.DEFAULT_PROVIDER
        name = "Google Gemini" if active == "gemini" else "OpenAI"
        status_text = f"Your Echo Pop assistant is online. Currently using {name} as the active model."
        return build_ask_response(
            text=status_text,
            reprompt_text="What would you like to ask?",
            session_attributes=session_attrs
        )

