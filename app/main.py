import json
import logging
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.alexa.models import AlexaRequestEnvelope
from app.alexa.verifier import verify_alexa_request
from app.alexa.intent_router import AlexaIntentRouter
from app.alexa.response_builder import build_error_response
from app.utils.latency import LatencyTracker
from mangum import Mangum

# Setup structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("alexa_ai.main")

app = FastAPI(
    title="Echo Pop Cloud AI Voice Assistant",
    version="1.0.0",
    description="Cloud AI assistant backend for Amazon Echo Pop using OpenAI and Google Gemini"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

intent_router = AlexaIntentRouter()

@app.get("/")
async def root():
    return {
        "service": "Echo Pop Cloud AI Assistant",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "default_provider": settings.DEFAULT_PROVIDER,
        "openai_model": settings.OPENAI_MODEL,
        "gemini_model": settings.GEMINI_MODEL,
        "signature_verification": settings.VERIFY_ALEXA_SIGNATURE,
        "persistence_enabled": settings.PERSISTENCE_ENABLED
    }

@app.post("/")
@app.post("/api/v1/alexa")
async def alexa_webhook(request: Request):
    tracker = LatencyTracker()
    raw_body = await request.body()
    
    if not raw_body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty request body")

    try:
        data = json.loads(raw_body.decode("utf-8"))
        envelope = AlexaRequestEnvelope.model_validate(data)
    except Exception as exc:
        logger.error(f"Failed to parse Alexa request payload: {exc}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Alexa request format")

    # Optional Skill ID validation
    if settings.ALEXA_SKILL_ID and envelope.session and envelope.session.application:
        app_id = envelope.session.application.applicationId
        if app_id != settings.ALEXA_SKILL_ID:
            logger.warning(f"Skill ID mismatch: got '{app_id}', expected '{settings.ALEXA_SKILL_ID}'")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Skill ID verification failed")

    # Verify signature and timestamp freshness (bypassed if VERIFY_ALEXA_SIGNATURE=False)
    await verify_alexa_request(request, raw_body, envelope.request.timestamp)

    try:
        response_envelope = await intent_router.handle_request(envelope, tracker=tracker)
    except Exception as exc:
        logger.error(f"Error processing intent: {exc}", exc_info=True)
        response_envelope = build_error_response("Sorry, an error occurred while processing your request.")

    metrics = tracker.finish()
    resp = JSONResponse(content=response_envelope.model_dump())
    resp.headers["X-Total-Latency-Ms"] = str(metrics["total_latency_ms"])
    resp.headers["X-AI-Latency-Ms"] = str(metrics["ai_latency_ms"])
    return resp

# AWS Lambda handler entrypoint
handler = Mangum(app)


