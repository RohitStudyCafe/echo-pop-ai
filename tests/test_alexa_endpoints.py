import pytest
from fastapi.testclient import TestClient
from app.main import app, intent_router
from app.providers.router import ProviderRouter
from tests.conftest import MockSuccessProvider

@pytest.fixture(autouse=True)
def setup_mock_router():
    # Inject mock providers into the global intent router for tests
    mock_openai = MockSuccessProvider("openai", "Mocked answer from OpenAI.")
    mock_gemini = MockSuccessProvider("gemini", "Mocked answer from Gemini.")
    intent_router.provider_router = ProviderRouter(
        openai_provider=mock_openai,
        gemini_provider=mock_gemini
    )

def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "default_provider" in data

def test_alexa_launch_request(sample_alexa_launch_payload):
    client = TestClient(app)
    response = client.post("/api/v1/alexa", json=sample_alexa_launch_payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["version"] == "1.0"
    speech = data["response"]["outputSpeech"]["text"]
    assert "Hi, I'm your cloud AI assistant" in speech
    assert data["response"]["shouldEndSession"] is False

def test_alexa_ask_ai_intent(sample_alexa_ask_payload):
    client = TestClient(app)
    response = client.post("/api/v1/alexa", json=sample_alexa_ask_payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["response"]["shouldEndSession"] is False
    speech = data["response"]["outputSpeech"]["text"]
    assert "Mocked answer from OpenAI" in speech
    
    # Verify session history was updated
    session_attrs = data.get("sessionAttributes", {})
    assert "chat_history" in session_attrs
    history = session_attrs["chat_history"]
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What is the speed of light?"
    assert history[1]["role"] == "assistant"

def test_alexa_switch_provider_intent(sample_alexa_ask_payload):
    client = TestClient(app)
    payload = dict(sample_alexa_ask_payload)
    payload["request"] = {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.switch",
        "timestamp": payload["request"]["timestamp"],
        "locale": "en-US",
        "intent": {
            "name": "SwitchProviderIntent",
            "confirmationStatus": "NONE",
            "slots": {
                "Provider": {"name": "Provider", "value": "gemini"}
            }
        }
    }
    response = client.post("/api/v1/alexa", json=payload)
    assert response.status_code == 200
    data = response.json()
    speech = data["response"]["outputSpeech"]["text"]
    assert "Switched provider to Google Gemini" in speech
    assert data["sessionAttributes"]["preferred_provider"] == "gemini"

def test_alexa_clear_memory_intent(sample_alexa_ask_payload):
    client = TestClient(app)
    payload = dict(sample_alexa_ask_payload)
    payload["session"]["attributes"] = {
        "chat_history": [{"role": "user", "content": "prior question"}]
    }
    payload["request"] = {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.clear",
        "timestamp": payload["request"]["timestamp"],
        "locale": "en-US",
        "intent": {
            "name": "ClearMemoryIntent",
            "confirmationStatus": "NONE"
        }
    }
    response = client.post("/api/v1/alexa", json=payload)
    assert response.status_code == 200
    data = response.json()
    speech = data["response"]["outputSpeech"]["text"]
    assert "cleared our conversation memory" in speech
    assert data["sessionAttributes"]["chat_history"] == []

def test_alexa_stop_intent(sample_alexa_ask_payload):
    client = TestClient(app)
    payload = dict(sample_alexa_ask_payload)
    payload["request"] = {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.stop",
        "timestamp": payload["request"]["timestamp"],
        "locale": "en-US",
        "intent": {
            "name": "AMAZON.StopIntent",
            "confirmationStatus": "NONE"
        }
    }
    response = client.post("/api/v1/alexa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["response"]["shouldEndSession"] is True
    assert "Goodbye" in data["response"]["outputSpeech"]["text"]

def test_alexa_help_intent(sample_alexa_ask_payload):
    client = TestClient(app)
    payload = dict(sample_alexa_ask_payload)
    payload["request"] = {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.help",
        "timestamp": payload["request"]["timestamp"],
        "locale": "en-US",
        "intent": {
            "name": "AMAZON.HelpIntent",
            "confirmationStatus": "NONE"
        }
    }
    response = client.post("/api/v1/alexa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["response"]["shouldEndSession"] is False
    assert "You can ask me any question" in data["response"]["outputSpeech"]["text"]

def test_alexa_get_status_intent(sample_alexa_ask_payload):
    client = TestClient(app)
    payload = dict(sample_alexa_ask_payload)
    payload["request"] = {
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.status",
        "timestamp": payload["request"]["timestamp"],
        "locale": "en-US",
        "intent": {
            "name": "GetStatusIntent",
            "confirmationStatus": "NONE"
        }
    }
    response = client.post("/api/v1/alexa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Your Echo Pop assistant is online" in data["response"]["outputSpeech"]["text"]

