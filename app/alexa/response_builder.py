from typing import Optional, Dict, Any
from .models import AlexaResponse, AlexaResponseEnvelope, OutputSpeech, Reprompt

def build_ask_response(
    text: str,
    reprompt_text: Optional[str] = None,
    session_attributes: Optional[Dict[str, Any]] = None
) -> AlexaResponseEnvelope:
    """Builds a response that keeps the Alexa session open for conversational follow-up."""
    speech = OutputSpeech(type="PlainText", text=text)
    reprompt = None
    if reprompt_text:
        reprompt = Reprompt(outputSpeech=OutputSpeech(type="PlainText", text=reprompt_text))
    
    response = AlexaResponse(
        outputSpeech=speech,
        reprompt=reprompt,
        shouldEndSession=False
    )
    return AlexaResponseEnvelope(
        version="1.0",
        sessionAttributes=session_attributes or {},
        response=response
    )

def build_tell_response(
    text: str,
    session_attributes: Optional[Dict[str, Any]] = None
) -> AlexaResponseEnvelope:
    """Builds a response that closes the Alexa session upon speaking."""
    speech = OutputSpeech(type="PlainText", text=text)
    response = AlexaResponse(
        outputSpeech=speech,
        shouldEndSession=True
    )
    return AlexaResponseEnvelope(
        version="1.0",
        sessionAttributes=session_attributes or {},
        response=response
    )

def build_error_response(
    message: str = "Sorry, I encountered an issue reaching the AI provider. Please try again in a moment."
) -> AlexaResponseEnvelope:
    """Graceful error response so Echo Pop speaks an apology rather than failing with silence."""
    return build_tell_response(text=message)
