import pytest
from app.providers.router import ProviderRouter
from app.providers.base import ChatMessage
from app.utils.latency import LatencyTracker
from tests.conftest import MockSuccessProvider, MockFailingProvider

@pytest.mark.asyncio
async def test_route_to_primary():
    openai_mock = MockSuccessProvider(name="openai", return_text="OpenAI answer")
    gemini_mock = MockSuccessProvider(name="gemini", return_text="Gemini answer")
    router = ProviderRouter(openai_provider=openai_mock, gemini_provider=gemini_mock)

    messages = [ChatMessage(role="user", content="Hello")]
    resp = await router.generate_with_fallback(messages, requested_provider="openai")
    
    assert resp.provider_name == "openai"
    assert resp.text == "OpenAI answer"
    assert openai_mock.call_count == 1
    assert gemini_mock.call_count == 0

@pytest.mark.asyncio
async def test_route_to_gemini():
    openai_mock = MockSuccessProvider(name="openai", return_text="OpenAI answer")
    gemini_mock = MockSuccessProvider(name="gemini", return_text="Gemini answer")
    router = ProviderRouter(openai_provider=openai_mock, gemini_provider=gemini_mock)

    messages = [ChatMessage(role="user", content="Hello")]
    resp = await router.generate_with_fallback(messages, requested_provider="gemini")
    
    assert resp.provider_name == "gemini"
    assert resp.text == "Gemini answer"
    assert gemini_mock.call_count == 1
    assert openai_mock.call_count == 0

@pytest.mark.asyncio
async def test_fallback_when_primary_fails():
    failing_openai = MockFailingProvider(name="openai")
    working_gemini = MockSuccessProvider(name="gemini", return_text="Gemini fallback answer")
    router = ProviderRouter(openai_provider=failing_openai, gemini_provider=working_gemini)

    tracker = LatencyTracker()
    messages = [ChatMessage(role="user", content="Test fallback")]
    
    resp = await router.generate_with_fallback(
        messages,
        requested_provider="openai",
        tracker=tracker
    )
    
    assert resp.provider_name == "gemini"
    assert resp.text == "Gemini fallback answer"
    assert tracker.fallback_triggered is True
    assert failing_openai.call_count == 1
    assert working_gemini.call_count == 1

@pytest.mark.asyncio
async def test_all_providers_failing_raises():
    failing_openai = MockFailingProvider(name="openai")
    failing_gemini = MockFailingProvider(name="gemini")
    router = ProviderRouter(openai_provider=failing_openai, gemini_provider=failing_gemini)

    messages = [ChatMessage(role="user", content="Test failure")]
    with pytest.raises(RuntimeError):
        await router.generate_with_fallback(messages, requested_provider="openai")

