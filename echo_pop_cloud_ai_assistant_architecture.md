# Echo Pop Cloud AI Voice Assistant — Architecture & Implementation Plan

## 1. Project goal

Build a cloud-hosted AI voice assistant for an Amazon Echo Pop using OpenAI and Google Gemini APIs.

Constraints:
- Use the Echo Pop's existing built-in microphone and speaker.
- Do not root, jailbreak, flash, or modify Echo Pop firmware.
- Do not connect USB or open the device.
- Do not require a personal computer to run continuously.
- Prefer free hosting; keep any unavoidable costs low.
- Support multiple AI providers and conversation memory.
- Optimize response latency.

## 2. Important platform limitation

A standard Alexa Custom Skill does **not** provide third-party developers with continuous raw microphone audio from the Echo Pop.

Alexa handles:
1. Wake-word detection.
2. Microphone capture.
3. Speech recognition (ASR).
4. Intent/request creation.
5. Sending the recognized request to the skill backend.
6. Speaking the skill's response.

Therefore, a VPS cannot receive the Echo Pop's raw microphone stream merely by opening a WebSocket.

A WebSocket connection between the VPS and an AI provider can be useful for supported provider workflows, but it does not bypass Alexa's microphone-access restrictions.

**What is achievable with an unmodified Echo Pop:**
- Fast turn-based AI conversations.
- OpenAI and Gemini provider routing.
- Conversation/session memory.
- Alexa native text-to-speech responses.
- Follow-up turns while Alexa keeps the skill session open.
- Potentially, hosted audio playback using Alexa AudioPlayer.

**What is not achievable through a standard Custom Skill alone:**
- ChatGPT Voice-style continuous full-duplex conversation.
- Direct raw microphone streaming from the Echo Pop to OpenAI Realtime or Gemini Live.
- Reliable natural interruption/barge-in while custom AI audio is playing, equivalent to a dedicated live voice client.

## 3. Recommended architecture

```text
Amazon Echo Pop
  |
  | Alexa wake word, microphone capture, ASR
  v
Alexa Cloud / Alexa Skills Kit
  |
  | HTTPS skill request (recognized text + session context)
  v
Cloud VPS
  |
  +--> FastAPI application
  |      |
  |      +--> Request validation and intent handling
  |      +--> AI provider router
  |      +--> Prompt/context builder
  |      +--> Response formatting
  |
  +--> Redis (optional)
  |      |
  |      +--> Short-lived session cache
  |
  +--> Persistent database
  |      |
  |      +--> Conversation history / user preferences
  |
  +--> OpenAI API
  |
  +--> Google Gemini API
  |
  v
Alexa skill response
  |
  +--> Alexa native speech output (recommended initial option)
  |
  +--> Optional AudioPlayer playback of hosted audio
```

## 4. Suggested technology stack

| Layer | Recommended technology | Purpose |
|---|---|---|
| Skill | Alexa Skills Kit | Echo interaction and intents |
| Backend | Python + FastAPI | Cloud API and business logic |
| Hosting | VPS or serverless platform | Always-available backend |
| AI provider 1 | OpenAI API | Main conversational model |
| AI provider 2 | Google Gemini API | Alternative model / fallback |
| Cache | Redis | Fast session lookups |
| Database | PostgreSQL or DynamoDB | Persistent memory |
| Deployment | Docker | Repeatable deployment |
| Monitoring | Structured logs + health endpoint | Debugging and latency tracking |

The VPS does not need a GPU because model inference is performed by the external AI providers.

## 5. Latency optimization

Prioritize these optimizations:

1. Select a VPS region with good network latency to the Alexa backend and AI provider endpoints. Test regions rather than assuming geographic proximity guarantees the fastest route.
2. Use asynchronous HTTP requests in FastAPI.
3. Reuse HTTP client connections where supported.
4. Keep prompts concise and limit unnecessary conversation history.
5. Store recent session context in Redis.
6. Use one AI provider per request by default. Do not call OpenAI and Gemini in parallel for every ordinary question.
7. Implement provider fallback only when the primary provider fails or times out.
8. Set sensible connection and response timeouts.
9. Keep Alexa responses concise so speech begins sooner.
10. Measure each stage separately.

Suggested latency measurements:
- Alexa request received timestamp.
- VPS request-processing start.
- AI request start.
- AI first-token / response completion time, depending on API.
- VPS response sent.
- Total backend processing time.

Note: Alexa's speech recognition and response playback add latency outside the VPS. The VPS cannot optimize those stages directly.

## 6. AI provider routing

Implement a provider abstraction so the rest of the application does not depend on one vendor.

Suggested routing policy:
- OpenAI: default conversational provider.
- Gemini: alternate provider or user-selected provider.
- Fallback: use the other provider if the selected provider is unavailable, subject to timeout and retry policy.
- Do not silently switch providers if doing so would violate a user's explicit model selection.
- Keep provider API keys in environment variables or a secrets manager. Never store keys in the Alexa skill model, source repository, or client-side code.

Example configuration:

```env
OPENAI_API_KEY=replace_me
OPENAI_MODEL=your_available_openai_model
GEMINI_API_KEY=replace_me
GEMINI_MODEL=your_available_gemini_model

REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:password@localhost:5432/echo_ai

DEFAULT_PROVIDER=openai
REQUEST_TIMEOUT_SECONDS=12
MAX_HISTORY_MESSAGES=12
```

Use model identifiers currently available to your API account; do not assume a model name from an old example is still available.

## 7. Conversation memory

Use two memory layers:

### Short-term session memory
- Current conversation turns.
- Stored in Alexa session attributes and/or Redis.
- Fast expiry, for example 30–60 minutes.
- Keep only the context needed for the next response.

### Long-term memory
- Explicit user preferences and facts the user wants the assistant to retain.
- Stored in a persistent database.
- Provide a way to inspect and clear memory.
- Avoid storing sensitive information unnecessarily.
- Apply a retention policy and protect stored data.

## 8. Voice output options

### Option A — Alexa native voice (recommended first)
The VPS returns text in the Alexa skill response. Alexa speaks it using its built-in speech output.

Advantages:
- Simplest integration.
- No separate audio hosting pipeline.
- Fits the normal Custom Skill interaction model.

Limitations:
- Not a continuous AI audio stream.
- Voice and prosody are controlled by Alexa.

### Option B — Hosted audio through Alexa AudioPlayer
The VPS or another service generates audio and exposes it at a supported HTTPS URL. The skill can ask Alexa AudioPlayer to play the stream where the device and skill interaction support it.

Advantages:
- More control over generated voice.
- Can use audio generated by an AI speech service.

Limitations:
- AudioPlayer is a playback feature, not a microphone streaming interface.
- It does not create full-duplex voice conversation.
- Interruption and microphone behavior remain subject to Alexa's platform rules.

Start with Option A. Evaluate Option B only after the basic skill is reliable.

## 9. Hosting and cost strategy

A small backend is sufficient:
- 1–2 vCPU.
- 1–2 GB RAM.
- Approximately 20 GB SSD.
- Ubuntu LTS.
- No GPU required.

Possible hosting approaches:
- Serverless functions for request-driven workloads.
- A low-cost VPS for a persistent FastAPI service and optional Redis.
- Free tiers where available, subject to eligibility, limits, and changing provider terms.

Do not assume a free VPS or free tier is permanently free. Set billing alerts, usage limits, and API spending caps where available.

Separate cost categories:
1. Hosting.
2. Database/cache.
3. OpenAI API usage.
4. Gemini API usage.
5. Domain name and any other optional services.

## 10. Security requirements

- Store provider API keys only on the backend.
- Validate Alexa request signatures and timestamps using the supported Alexa Skills Kit verification approach.
- Use HTTPS for the skill endpoint.
- Authenticate internal administration endpoints.
- Never log full API keys, access tokens, or unnecessary personal conversation content.
- Apply request rate limits and maximum input/output sizes.
- Use least-privilege database credentials.
- Keep dependencies updated.
- Configure backups and a memory deletion process.

## 11. Implementation phases

### Phase 1 — Working Alexa skill
- Create an Alexa Custom Skill.
- Define Launch, AskAI, Help, and ClearMemory intents.
- Connect the skill to a minimal HTTPS backend.
- Return a short static response to verify end-to-end behavior.

### Phase 2 — AI integration
- Add OpenAI API support.
- Add Gemini API support.
- Implement provider selection and fallback.
- Add timeout handling and safe error messages.

### Phase 3 — Memory
- Add session memory.
- Add persistent conversation memory.
- Add a clear-memory intent.
- Test session expiry and provider switching.

### Phase 4 — Latency and reliability
- Add asynchronous requests and connection reuse.
- Add Redis if measurements justify it.
- Record per-stage latency.
- Test timeouts, provider outages, and rate limits.
- Tune response length and context size.

### Phase 5 — Optional custom voice
- Evaluate Alexa AudioPlayer compatibility.
- Generate speech audio through a provider.
- Host audio over HTTPS.
- Test playback, stop behavior, and Alexa session handling.
- Do not treat this as a full-duplex solution.

## 12. Acceptance criteria

The first production-ready version should:
- Work on the unmodified Echo Pop.
- Require no USB connection or device disassembly.
- Require no personal computer to remain on.
- Reach the cloud backend securely.
- Answer using at least one AI provider.
- Support both OpenAI and Gemini through configuration.
- Preserve short-term conversation context.
- Allow the user to clear stored memory.
- Handle provider timeouts gracefully.
- Record backend latency without exposing secrets.
- Clearly communicate that the experience is turn-based, not full-duplex live voice.

## 13. Final recommendation

Build the first version using:

**Echo Pop + Alexa Custom Skill + Python FastAPI + OpenAI/Gemini + Redis (if needed) + persistent memory.**

Use Alexa's native voice initially. Optimize the backend and measure real end-to-end response times before adding more infrastructure.

A VPS and WebSockets can improve the cloud-side architecture, but they cannot provide raw Echo Pop microphone audio through a standard Alexa Custom Skill. True ChatGPT Voice-style full-duplex operation would require a separate supported microphone/audio client or a verified device-level modification, neither of which is part of this plan.

---

## Useful official documentation

- Alexa Skills Kit: https://developer.amazon.com/en-US/alexa/alexa-skills-kit
- Alexa Skills Kit request/response: https://developer.amazon.com/en-US/docs/alexa/custom-skills/request-and-response-json-reference.html
- Alexa AudioPlayer: https://developer.amazon.com/en-US/docs/alexa/custom-skills/audioplayer-interface-reference.html
- OpenAI API documentation: https://platform.openai.com/docs/
- OpenAI Realtime API: https://platform.openai.com/docs/guides/realtime
- Gemini API documentation: https://ai.google.dev/gemini-api/docs
- FastAPI documentation: https://fastapi.tiangolo.com/
