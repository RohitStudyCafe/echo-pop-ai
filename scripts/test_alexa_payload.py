#!/usr/bin/env python3
"""
CLI utility to simulate standard Alexa JSON requests against the local FastAPI server.
Usage:
    python scripts/test_alexa_payload.py launch
    python scripts/test_alexa_payload.py ask "Why is the sky blue?"
    python scripts/test_alexa_payload.py switch "gemini"
    python scripts/test_alexa_payload.py clear
"""
import sys
import json
import datetime
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1/alexa"

def create_base_envelope(request_body: dict, session_attrs: dict = None) -> dict:
    return {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": "amzn1.echo-api.session.test-session-1234",
            "application": {"applicationId": "amzn1.ask.skill.test-skill"},
            "attributes": session_attrs or {},
            "user": {"userId": "amzn1.ask.account.test-user"}
        },
        "context": {
            "System": {
                "application": {"applicationId": "amzn1.ask.skill.test-skill"},
                "user": {"userId": "amzn1.ask.account.test-user"}
            }
        },
        "request": request_body
    }

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if cmd == "launch":
        envelope = create_base_envelope({
            "type": "LaunchRequest",
            "requestId": "amzn1.echo-api.request.launch-123",
            "timestamp": ts,
            "locale": "en-US"
        })
    elif cmd == "ask":
        query = sys.argv[2] if len(sys.argv) > 2 else "What is quantum computing?"
        envelope = create_base_envelope({
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.ask-123",
            "timestamp": ts,
            "locale": "en-US",
            "intent": {
                "name": "AskAIIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "Query": {"name": "Query", "value": query}
                }
            }
        })
    elif cmd == "switch":
        provider = sys.argv[2] if len(sys.argv) > 2 else "gemini"
        envelope = create_base_envelope({
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.switch-123",
            "timestamp": ts,
            "locale": "en-US",
            "intent": {
                "name": "SwitchProviderIntent",
                "confirmationStatus": "NONE",
                "slots": {
                    "Provider": {"name": "Provider", "value": provider}
                }
            }
        })
    elif cmd == "clear":
        envelope = create_base_envelope({
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.clear-123",
            "timestamp": ts,
            "locale": "en-US",
            "intent": {
                "name": "ClearMemoryIntent",
                "confirmationStatus": "NONE"
            }
        })
    else:
        print(f"Unknown command '{cmd}'. Available: launch, ask, switch, clear")
        return

    print(f"--> Sending payload to {BASE_URL}...")
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(BASE_URL, json=envelope)
            print(f"<-- Status: {resp.status_code}")
            print(f"<-- Headers: Total-Latency: {resp.headers.get('X-Total-Latency-Ms')}ms, AI-Latency: {resp.headers.get('X-AI-Latency-Ms')}ms")
            print(f"<-- Response JSON:\n{json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    main()

