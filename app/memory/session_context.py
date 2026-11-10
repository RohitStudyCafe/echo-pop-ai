from typing import Dict, Any, List, Optional
from app.providers.base import ChatMessage
from app.config import settings

SESSION_HISTORY_KEY = "chat_history"
SESSION_PROVIDER_KEY = "preferred_provider"

def get_history_from_session(session_attributes: Optional[Dict[str, Any]]) -> List[ChatMessage]:
    """Extracts recent conversation turns from Alexa session attributes."""
    if not session_attributes:
        return []
    
    raw_history = session_attributes.get(SESSION_HISTORY_KEY, [])
    messages: List[ChatMessage] = []
    for item in raw_history:
        if isinstance(item, dict) and "role" in item and "content" in item:
            messages.append(ChatMessage(role=item["role"], content=item["content"]))
    return messages

def append_to_session_history(
    session_attributes: Optional[Dict[str, Any]],
    role: str,
    content: str,
    max_messages: Optional[int] = None
) -> Dict[str, Any]:
    """Appends a new turn and maintains a sliding window of max_messages turns."""
    max_count = max_messages or settings.MAX_HISTORY_MESSAGES
    attrs = dict(session_attributes or {})
    raw_history = list(attrs.get(SESSION_HISTORY_KEY, []))
    
    raw_history.append({"role": role, "content": content})
    
    # Enforce sliding window to minimize token overhead and latency
    if len(raw_history) > max_count:
        raw_history = raw_history[-max_count:]
        
    attrs[SESSION_HISTORY_KEY] = raw_history
    return attrs

def clear_session_history(session_attributes: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Clears conversation history while preserving other session preferences."""
    attrs = dict(session_attributes or {})
    attrs[SESSION_HISTORY_KEY] = []
    return attrs

def get_preferred_provider(session_attributes: Optional[Dict[str, Any]]) -> Optional[str]:
    """Retrieves session-selected AI provider preference if set."""
    if not session_attributes:
        return None
    return session_attributes.get(SESSION_PROVIDER_KEY)

def set_preferred_provider(session_attributes: Optional[Dict[str, Any]], provider: str) -> Dict[str, Any]:
    """Updates preferred AI provider in session attributes."""
    attrs = dict(session_attributes or {})
    attrs[SESSION_PROVIDER_KEY] = provider.strip().lower()
    return attrs

