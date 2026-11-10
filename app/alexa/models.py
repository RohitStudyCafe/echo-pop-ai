from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class AlexaApplication(BaseModel):
    applicationId: Optional[str] = None

class AlexaUser(BaseModel):
    userId: Optional[str] = None
    accessToken: Optional[str] = None

class AlexaSession(BaseModel):
    new: Optional[bool] = False
    sessionId: Optional[str] = None
    application: Optional[AlexaApplication] = None
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user: Optional[AlexaUser] = None

class AlexaSlotValue(BaseModel):
    name: Optional[str] = None
    value: Optional[str] = None
    resolutions: Optional[Dict[str, Any]] = None

class AlexaIntent(BaseModel):
    name: str
    confirmationStatus: Optional[str] = None
    slots: Optional[Dict[str, Dict[str, Any]]] = Field(default_factory=dict)

class AlexaRequest(BaseModel):
    type: str
    requestId: str
    timestamp: str
    locale: Optional[str] = "en-US"
    intent: Optional[AlexaIntent] = None
    reason: Optional[str] = None

class AlexaSystemContext(BaseModel):
    application: Optional[AlexaApplication] = None
    user: Optional[AlexaUser] = None

class AlexaContext(BaseModel):
    System: Optional[AlexaSystemContext] = None

class AlexaRequestEnvelope(BaseModel):
    version: str = "1.0"
    session: Optional[AlexaSession] = None
    context: Optional[AlexaContext] = None
    request: AlexaRequest

class OutputSpeech(BaseModel):
    type: str = "PlainText"
    text: Optional[str] = None
    ssml: Optional[str] = None

class Reprompt(BaseModel):
    outputSpeech: OutputSpeech

class AlexaResponse(BaseModel):
    outputSpeech: Optional[OutputSpeech] = None
    reprompt: Optional[Reprompt] = None
    shouldEndSession: bool = True

class AlexaResponseEnvelope(BaseModel):
    version: str = "1.0"
    sessionAttributes: Dict[str, Any] = Field(default_factory=dict)
    response: AlexaResponse
