import pytest
import datetime
from typing import Dict, Any
from app.providers.base import BaseAIProvider, ProviderResponse, ChatMessage

class MockSuccessProvider(BaseAIProvider):
    def __init__(self, name: str = "mock_provider", return_text: str = "This is a mock AI response."):
        self.name = name
        self.return_text = return_text
        self.call_count = 0

    async def generate_response(self, messages, system_prompt=None, timeout_seconds=None):
        self.call_count += 1
        return ProviderResponse(
            text=self.return_text,
            provider_name=self.name,
            model_name="mock-model-v1",
            latency_ms=120.5
        )

class MockFailingProvider(BaseAIProvider):
    def __init__(self, name: str = "failing_provider"):
        self.name = name
        self.call_count = 0

    async def generate_response(self, messages, system_prompt=None, timeout_seconds=None):
        self.call_count += 1
        raise TimeoutError("Provider timed out")

@pytest.fixture
def sample_alexa_launch_payload() -> Dict[str, Any]:
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "version": "1.0",
        "session": {
            "new": True,
            "sessionId": "amzn1.echo-api.session.test-123",
            "application": {"applicationId": "amzn1.ask.skill.test"},
            "attributes": {},
            "user": {"userId": "amzn1.ask.account.user-123"}
        },
        "context": {
            "System": {
                "application": {"applicationId": "amzn1.ask.skill.test"},
                "user": {"userId": "amzn1.ask.account.user-123"}
            }
        },
        "request": {
            "type": "LaunchRequest",
            "requestId": "amzn1.echo-api.request.req-1",
            "timestamp": ts,
            "locale": "en-US"
        }
    }

@pytest.fixture
def sample_alexa_ask_payload() -> Dict[str, Any]:
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": "amzn1.echo-api.session.test-123",
            "application": {"applicationId": "amzn1.ask.skill.test"},
            "attributes": {},
            "user": {"userId": "amzn1.ask.account.user-123"}
        },
        "context": {
            "System": {
                "application": {"applicationId": "amzn1.ask.skill.test"},
                "user": {"userId": "amzn1.ask.account.user-123"}
            }
        },
        "request": {
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.req-2",
            "timestamp": ts,
            "locale": "en-US",
            "intent": {
                "name": "AskAIIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "Query": {
                        "name": "Query",
                        "value": "What is the speed of light?"
                    }
                }
            }
        }
    }

